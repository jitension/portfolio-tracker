"""
Robinhood API client wrapper using robin-stocks library.
Handles authentication, 2FA, and data fetching from Robinhood.
"""
import robin_stocks.robinhood as rh
from typing import Dict, Optional
import logging
import time
from core.encryption import decrypt_credentials
from core.exceptions import (
    RobinhoodAPIError,
    CredentialDecryptionError,
    MFARequiredError
)

logger = logging.getLogger('apps')
security_logger = logging.getLogger('security')


class RobinhoodClient:
    """
    Wrapper around robin-stocks library for Robinhood API integration.
    
    Features:
    - Secure authentication with encrypted credentials
    - 2FA/MFA support (SMS and authenticator app)
    - Portfolio data fetching
    - Holdings retrieval
    - Transaction history
    - Error handling and logging
    """
    
    def __init__(self, robinhood_account=None):
        """
        Initialize Robinhood client.
        
        Args:
            robinhood_account: RobinhoodAccount instance (optional)
        """
        self.account = robinhood_account
        self.is_authenticated = False
        self.session_active = False
    
    def _ensure_session(self):
        """
        Ensure robin-stocks has an active session before making API calls.
        
        This method MUST be called before every robin_stocks API call to guarantee
        the session is active, especially in multi-process/container environments
        where in-memory state doesn't persist between requests.
        
        Raises:
            RobinhoodAPIError: If session cannot be established
        """
        from django.utils import timezone
        from robin_stocks.robinhood.helper import update_session, set_login_state
        
        # First check if we already have an active session from a recent authentication
        # This happens during link_account() flow where authenticate() just succeeded
        if self.session_active:
            logger.debug("Session already active, skipping restoration")
            return
        
        # Check if we have an account with stored token
        if not self.account or not self.account.auth_token_encrypted:
            raise RobinhoodAPIError("No stored authentication token available. Please log in first.")
        
        # Check if token is expired
        if self.account.token_expires_at and self.account.token_expires_at <= timezone.now():
            raise RobinhoodAPIError(f"Authentication token expired. Please log in again.")
        
        try:
            # Decrypt stored token
            token_data = decrypt_credentials(self.account.auth_token_encrypted)
            
            # Extract token components
            access_token = token_data.get('access_token')
            token_type = token_data.get('token_type', 'Bearer')
            
            if not access_token:
                raise RobinhoodAPIError("No access_token found in stored credentials")
            
            # Restore the OAuth token in robin-stocks session
            update_session('Authorization', f"{token_type} {access_token}")
            set_login_state(True)
            
            logger.debug(f"Session restored for account {self.account.account_number}")
            self.is_authenticated = True
            self.session_active = True
        
        except CredentialDecryptionError as e:
            logger.error(f"Failed to decrypt credentials: {str(e)}")
            raise RobinhoodAPIError("Failed to decrypt stored credentials") from e
        except Exception as e:
            logger.error(f"Failed to restore session: {str(e)}")
            raise RobinhoodAPIError(f"Failed to establish session: {str(e)}") from e
    
    def _handle_verification_workflow(self, device_token: str, workflow_id: str):
        """
        Handle Robinhood's verification workflow for push notifications.
        
        Args:
            device_token: The device token generated for this session
            workflow_id: The workflow ID from the verification_workflow response
            
        Raises:
            RobinhoodAPIError: If verification fails or times out
        """
        import requests
        
        logger.info(f"Starting verification workflow with ID: {workflow_id}")
        
        # Step 1: POST to pathfinder/user_machine to register the verification
        pathfinder_url = "https://api.robinhood.com/pathfinder/user_machine/"
        machine_payload = {
            'device_id': device_token,
            'flow': 'suv',
            'input': {'workflow_id': workflow_id}
        }
        
        try:
            machine_response = requests.post(pathfinder_url, json=machine_payload, timeout=15)
            machine_data = machine_response.json()
            
            if 'id' not in machine_data:
                raise RobinhoodAPIError("No verification ID returned from Robinhood")
            
            machine_id = machine_data['id']
            logger.info(f"Machine ID obtained: {machine_id}")
        
        except Exception as e:
            logger.error(f"Failed to register verification workflow: {str(e)}")
            raise RobinhoodAPIError(f"Verification workflow failed: {str(e)}")
        
        # Step 2: Poll the inquiries endpoint to get challenge details
        inquiries_url = f"https://api.robinhood.com/pathfinder/inquiries/{machine_id}/user_view/"
        start_time = time.time()
        timeout = 120  # 2 minute timeout
        
        challenge_id = None
        
        while time.time() - start_time < timeout:
            time.sleep(5)
            
            try:
                inquiries_response = requests.get(inquiries_url, timeout=15)
                
                if inquiries_response.status_code != 200:
                    logger.warning(f"Inquiries request returned {inquiries_response.status_code}")
                    continue
                
                inquiries_data = inquiries_response.json()
                
                # Check for sheriff_challenge
                if 'context' in inquiries_data and 'sheriff_challenge' in inquiries_data['context']:
                    challenge = inquiries_data['context']['sheriff_challenge']
                    challenge_type = challenge.get('type')
                    challenge_status = challenge.get('status')
                    challenge_id = challenge.get('id')
                    
                    logger.info(f"Challenge found: type={challenge_type}, status={challenge_status}, id={challenge_id}")
                    
                    # If it's a prompt (push notification), poll for approval
                    if challenge_type == "prompt":
                        logger.info("📱 Push notification sent! Waiting for approval on Robinhood app...")
                        prompt_url = f"https://api.robinhood.com/push/{challenge_id}/get_prompts_status/"
                        
                        # Poll the prompt status
                        prompt_start = time.time()
                        while time.time() - prompt_start < timeout:
                            time.sleep(5)
                            
                            try:
                                prompt_response = requests.get(prompt_url, timeout=15)
                                prompt_data = prompt_response.json()
                                
                                if prompt_data.get('challenge_status') == 'validated':
                                    logger.info("✓ Push notification approved!")
                                    break
                                else:
                                    logger.info(f"Waiting for approval... (status: {prompt_data.get('challenge_status')})")
                            
                            except Exception as e:
                                logger.warning(f"Error checking prompt status: {str(e)}")
                                continue
                        
                        break
                    
                    elif challenge_status == "validated":
                        logger.info("Challenge already validated!")
                        break
            
            except Exception as e:
                logger.warning(f"Error polling inquiries: {str(e)}")
                continue
        
        # Step 3: Final verification - poll workflow status
        logger.info("Checking final workflow status...")
        inquiries_payload = {"sequence": 0, "user_input": {"status": "continue"}}
        
        retry_attempts = 5
        while time.time() - start_time < timeout and retry_attempts > 0:
            try:
                final_response = requests.post(inquiries_url, json=inquiries_payload, timeout=15)
                final_data = final_response.json()
                
                if 'type_context' in final_data:
                    result = final_data['type_context'].get('result')
                    if result == 'workflow_status_approved':
                        logger.info("✓ Verification workflow approved!")
                        return
                
                # Check verification_workflow status
                workflow_status = final_data.get('verification_workflow', {}).get('workflow_status')
                if workflow_status == 'workflow_status_approved':
                    logger.info("✓ Workflow status approved!")
                    return
                elif workflow_status == 'workflow_status_internal_pending':
                    logger.info("Still waiting for final approval...")
                
                time.sleep(5)
                retry_attempts -= 1
            
            except Exception as e:
                logger.warning(f"Error checking final status: {str(e)}")
                retry_attempts -= 1
                time.sleep(5)
        
        # If we got here, assume approval (robin-stocks does this)
        logger.warning("Verification check timed out, assuming approval and proceeding...")
    
    def authenticate(self, username: str = None, password: str = None, 
                    mfa_code: str = None, force_fresh_login: bool = False) -> Dict:
        """
        Authenticate with Robinhood API with token persistence.
        
        Args:
            username: Robinhood email/username (if not using stored credentials)
            password: Robinhood password (if not using stored credentials)
            mfa_code: 2FA code (required if MFA is enabled)
            force_fresh_login: Force a fresh login even if token exists
        
        Returns:
            Dict with authentication result
        
        Raises:
            RobinhoodAPIError: If authentication fails
            MFARequiredError: If MFA code is required but not provided
            CredentialDecryptionError: If stored credentials can't be decrypted
        """
        from django.utils import timezone
        from datetime import timedelta
        from core.encryption import encrypt_credentials, decrypt_credentials
        
        try:
            # Try to use stored token if available and not expired
            if not force_fresh_login and self.account and self.account.auth_token_encrypted:
                if self.account.token_expires_at and self.account.token_expires_at > timezone.now():
                    try:
                        # Decrypt and use stored token
                        token_data = decrypt_credentials(self.account.auth_token_encrypted)
                        
                        # Set the token in robin-stocks session
                        # Note: robin-stocks stores token internally
                        import pickle
                        import os
                        
                        # robin-stocks uses pickle to store session
                        # We'll try to restore the session
                        logger.info(f"Attempting to use stored token for {self.account.account_number}")
                        
                        # Test if token is still valid by making a simple API call
                        try:
                            test_profile = rh.load_account_profile()
                            if test_profile and isinstance(test_profile, dict) and test_profile.get('url'):
                                self.is_authenticated = True
                                self.session_active = True
                                logger.info(f"Successfully authenticated using stored token")
                                return {
                                    'success': True,
                                    'message': 'Authenticated with stored token',
                                    'access_token': 'cached_session',
                                    'detail': 'Using cached authentication token'
                                }
                        except:
                            logger.info("Stored token invalid or expired, will perform fresh login")
                            pass
                    except Exception as e:
                        logger.warning(f"Failed to use stored token: {str(e)}, performing fresh login")
            # Use stored credentials if available
            if self.account and not (username and password):
                try:
                    credentials = decrypt_credentials(
                        self.account.credentials_encrypted
                    )
                    username = credentials['username']
                    password = credentials['password']
                except Exception as e:
                    logger.error(f"Credential decryption failed: {str(e)}")
                    raise CredentialDecryptionError(
                        "Failed to decrypt stored credentials"
                    )
            
            # Attempt login
            logger.info(f"=== Starting Robinhood Authentication ===")
            logger.info(f"Username: {username}")
            logger.info(f"MFA code provided: {bool(mfa_code)}")
            logger.info(f"MFA code value (first 2 chars): {mfa_code[:2] if mfa_code else 'None'}")
            
            # Use rh.login() as designed
            logger.info("Calling rh.login() with parameters:")
            login_params = {
                'username': username,
                'password': '***' if password else None,
                'expiresIn': 86400,
                'scope': 'internal',
                'by_sms': True,
                'store_session': True,
                'mfa_code': mfa_code
            }
            logger.info(f"Login parameters: {login_params}")
            
            # Attempt login using direct API call (following robin-stocks pattern)
            import requests
            import secrets
            
            # Generate device token (cryptographically secure)
            def generate_device_token():
                rands = [secrets.randbelow(256) for _ in range(16)]
                hexa = [str(hex(i + 256)).lstrip("0x")[1:] for i in range(256)]
                token = ""
                for i, r in enumerate(rands):
                    token += hexa[r]
                    if i in [3, 5, 7, 9]:
                        token += "-"
                return token
            
            device_token = generate_device_token()
            login_url = "https://api.robinhood.com/oauth2/token/"
            
            # Correct payload following robin-stocks implementation
            payload = {
                'client_id': 'c82SH0WZOsabOXGP2sxqcj34FxkvfnWRZBKlBjFS',
                'expires_in': 86400,
                'grant_type': 'password',
                'password': password,
                'scope': 'internal',
                'username': username,
                'device_token': device_token,
                'try_passkeys': False,
                'token_request_path': '/login',
                'create_read_only_secondary_token': True,
            }
            
            if mfa_code:
                payload['mfa_code'] = mfa_code
            
            logger.info(f"Attempting login to Robinhood API...")
            
            try:
                response = requests.post(login_url, json=payload, timeout=30)
                logger.info(f"Response status code: {response.status_code}")
                
                try:
                    login_result = response.json()
                    logger.info(f"Response keys: {list(login_result.keys())}")
                except ValueError as e:
                    logger.error(f"Could not parse response as JSON: {str(e)}")
                    raise RobinhoodAPIError(f"Invalid JSON response from Robinhood: {response.text}")
                
                # Check if verification workflow is required
                if 'verification_workflow' in login_result:
                    logger.info("Verification workflow required - handling push notification...")
                    workflow_id = login_result['verification_workflow']['id']
                    
                    # Handle the verification workflow
                    self._handle_verification_workflow(device_token, workflow_id)
                    
                    # Retry login after verification
                    logger.info("Retrying login after verification approval...")
                    response = requests.post(login_url, json=payload, timeout=30)
                    login_result = response.json()
                
                # Check if we got an access token
                if 'access_token' in login_result:
                    self.is_authenticated = True
                    self.session_active = True
                    
                    # Initialize robin-stocks session
                    from robin_stocks.robinhood.helper import update_session, set_login_state
                    update_session('Authorization', f"{login_result['token_type']} {login_result['access_token']}")
                    set_login_state(True)
                    
                    logger.info(f"✓ Authentication successful!")
                    
                    # Store the actual OAuth access token for session restoration
                    if self.account:
                        try:
                            from core.encryption import CredentialEncryption
                            encryption = CredentialEncryption()
                            # Store the real OAuth token
                            token_data = {
                                'access_token': login_result['access_token'],
                                'token_type': login_result.get('token_type', 'Bearer'),
                                'username': username
                            }
                            self.account.auth_token_encrypted = encryption.encrypt(token_data)
                            self.account.token_expires_at = timezone.now() + timedelta(hours=24)
                            self.account.save()
                            logger.info(f"Stored OAuth access token for session restoration")
                        except Exception as e:
                            logger.warning(f"Failed to store OAuth token: {str(e)}")
                    
                    return {
                        'success': True,
                        'message': 'Authentication successful',
                        'access_token': login_result.get('access_token'),
                        'detail': login_result.get('detail', 'Logged in successfully')
                    }
                else:
                    logger.error(f"Login failed - no access token in response")
                    logger.error(f"Response: {login_result}")
                    error_msg = login_result.get('detail', 'Authentication failed')
                    raise RobinhoodAPIError(f"Login failed: {error_msg}")
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {str(e)}")
                raise RobinhoodAPIError(f"Failed to connect to Robinhood: {str(e)}")
        
        except MFARequiredError:
            raise
        
        except CredentialDecryptionError:
            raise
        
        except Exception as e:
            logger.error(
                f"Robinhood authentication error: {str(e)}",
                exc_info=True
            )
            raise RobinhoodAPIError(f"Authentication failed: {str(e)}")
    
    def logout(self):
        """Logout from Robinhood."""
        try:
            rh.logout()
            self.is_authenticated = False
            self.session_active = False
            logger.info("Robinhood session logged out")
        except Exception as e:
            logger.warning(f"Robinhood logout error: {str(e)}")
    
    def get_account_info(self) -> Dict:
        """
        Get Robinhood account information.
        
        Returns:
            Dict with account details
        
        Raises:
            RobinhoodAPIError: If not authenticated or API error
        """
        # Ensure session is active before API call
        self._ensure_session()
        
        try:
            account_profile = rh.load_account_profile()
            return account_profile if account_profile else {}
        
        except Exception as e:
            logger.error(f"Failed to fetch account info: {str(e)}")
            raise RobinhoodAPIError(f"Failed to fetch account info: {str(e)}")
    
    def get_portfolio_summary(self) -> Dict:
        """
        Get portfolio summary/profile.
        
        Returns:
            Dict with portfolio data (equity, market value, etc.)
        """
        # Ensure session is active before API call
        self._ensure_session()
        
        try:
            portfolio = rh.load_portfolio_profile()
            return portfolio if portfolio else {}
        
        except Exception as e:
            logger.error(f"Failed to fetch portfolio: {str(e)}")
            raise RobinhoodAPIError(f"Failed to fetch portfolio: {str(e)}")
    
    def get_holdings(self) -> Dict:
        """
        Get current holdings (stocks, options, crypto).
        
        Returns:
            Dict with holdings categorized by type
        """
        # Ensure session is active before API call
        self._ensure_session()
        
        try:
            # Get stocks
            stock_positions = rh.get_open_stock_positions()
            
            # Get options
            option_positions = rh.get_open_option_positions()
            
            # Get crypto
            crypto_positions = rh.get_crypto_positions()
            
            return {
                'stocks': stock_positions or [],
                'options': option_positions or [],
                'crypto': crypto_positions or []
            }
        
        except Exception as e:
            logger.error(f"Failed to fetch holdings: {str(e)}")
            raise RobinhoodAPIError(f"Failed to fetch holdings: {str(e)}")
    
    def get_portfolio(self) -> Dict:
        """
        Get portfolio data (alias for get_portfolio_summary).
        
        Returns:
            Dict with portfolio data
        """
        return self.get_portfolio_summary()
    
    def get_stock_positions(self) -> list:
        """
        Get open stock positions with enhanced data.
        
        Returns:
            List of stock position dictionaries
        """
        # Ensure session is active before API call
        self._ensure_session()
        
        try:
            positions = rh.get_open_stock_positions()
            
            if not positions:
                return []
            
            # Enhance each position with additional data
            enhanced_positions = []
            for position in positions:
                try:
                    # Get instrument data for symbol
                    instrument_url = position.get('instrument')
                    if instrument_url:
                        instrument_data = rh.request_get(instrument_url)
                        if instrument_data:
                            position['symbol'] = instrument_data.get('symbol', '')
                            position['name'] = instrument_data.get('simple_name', '')
                    
                    # Get current price
                    symbol = position.get('symbol', '')
                    if symbol:
                        quote = self.get_stock_quote(symbol)
                        if quote:
                            position['current_price'] = quote.get('last_trade_price', '0')
                    
                    enhanced_positions.append(position)
                    
                except Exception as e:
                    logger.warning(f"Failed to enhance position data: {str(e)}")
                    enhanced_positions.append(position)
            
            return enhanced_positions
        
        except Exception as e:
            logger.error(f"Failed to fetch stock positions: {str(e)}")
            raise RobinhoodAPIError(f"Failed to fetch stock positions: {str(e)}")
    
    def get_margin_interest(self) -> Optional[Dict]:
        """
        Get margin account information.
        
        Returns:
            Dict with margin data including:
            - margin_limit: Total margin credit available
            - unallocated_margin_cash: Unused margin
            - outstanding_interest: Interest owed on margin
            - cash: Cash balance
            Returns None if account is not a margin account
        """
        # Ensure session is active before API call
        self._ensure_session()
        
        try:
            # robin-stocks method to get margin data
            margin_data = rh.load_account_profile(info=None)
            
            if not margin_data:
                logger.warning("No margin data available - may be a cash account")
                return None
            
            # Check if this is a margin account
            account_type = margin_data.get('type', 'cash')
            if account_type == 'cash':
                logger.info("Account is a cash account, not a margin account")
                return {
                    'is_margin_account': False,
                    'margin_limit': 0,
                    'unallocated_margin_cash': 0,
                    'outstanding_interest': 0,
                    'cash': float(margin_data.get('cash', 0))
                }
            
            # Extract margin-specific data
            return {
                'is_margin_account': True,
                'margin_limit': float(margin_data.get('margin_limit', 0)),
                'unallocated_margin_cash': float(margin_data.get('unallocated_margin_cash', 0)),
                'outstanding_interest': float(margin_data.get('margin_balances', {}).get('outstanding_interest', 0)),
                'cash': float(margin_data.get('cash', 0)),
                'buying_power': float(margin_data.get('buying_power', 0))
            }
        
        except Exception as e:
            logger.warning(f"Failed to fetch margin data: {str(e)}")
            return None
    
    def get_stock_quote(self, symbol: str) -> Optional[Dict]:
        """
        Get real-time quote for a stock symbol with previous_close.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Dict with quote data including previous_close or None if not found
        """
        # Ensure session is active before API call
        self._ensure_session()
        
        try:
            # Use get_quotes for detailed data including previous_close
            quotes = rh.get_quotes(symbol)
            if quotes and isinstance(quotes, list) and len(quotes) > 0:
                quote = quotes[0]
                # Ensure we have the key fields
                return {
                    'symbol': quote.get('symbol', symbol),
                    'last_trade_price': quote.get('last_trade_price', '0'),
                    'last_extended_hours_trade_price': quote.get('last_extended_hours_trade_price'),
                    'previous_close': quote.get('previous_close', '0'),
                    'adjusted_previous_close': quote.get('adjusted_previous_close', '0'),
                    'bid_price': quote.get('bid_price'),
                    'ask_price': quote.get('ask_price'),
                    'trading_halted': quote.get('trading_halted', False),
                    'has_traded': quote.get('has_traded', False),
                }
            
            # Fallback to get_latest_price if get_quotes fails
            price = rh.get_latest_price(symbol, includeExtendedHours=True)
            if price and isinstance(price, list) and len(price) > 0:
                return {
                    'symbol': symbol,
                    'last_trade_price': price[0],
                    'previous_close': '0'  # Not available from this endpoint
                }
            
            return None
        
        except Exception as e:
            logger.warning(f"Failed to fetch quote for {symbol}: {str(e)}")
            return None
    
    def test_connection(self, mfa_code: str = None) -> bool:
        """
        Test if stored credentials are still valid.
        
        Args:
            mfa_code: 2FA code if MFA is enabled
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.authenticate(mfa_code=mfa_code)
            # Try to fetch basic account info
            account_info = self.get_account_info()
            return bool(account_info)
        
        except Exception as e:
            logger.warning(f"Connection test failed: {str(e)}")
            return False
        
        finally:
            self.logout()
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensure logout."""
        self.logout()
        return False


def create_robinhood_client(robinhood_account) -> RobinhoodClient:
    """
    Factory function to create a RobinhoodClient instance.
    
    Args:
        robinhood_account: RobinhoodAccount model instance
    
    Returns:
        RobinhoodClient instance
    """
    return RobinhoodClient(robinhood_account)
