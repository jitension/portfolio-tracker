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
            logger.info(f"Attempting Robinhood login for: {username}")
            
            # robin-stocks 3.4.0 API
            # Note: For push notification, don't pass mfa_code
            if mfa_code:
                login_result = rh.login(
                    username=username,
                    password=password,
                    expiresIn=86400,
                    store_session=True,  # Enable session persistence
                    mfa_code=mfa_code
                )
            else:
                # No MFA code - let Robinhood handle push notification
                login_result = rh.login(
                    username=username,
                    password=password,
                    expiresIn=86400,
                    store_session=True  # Enable session persistence
                )
            
            # Log response for debugging
            logger.info(f"Robinhood login result type: {type(login_result)}, value: {login_result}")
            
            # robin-stocks may return None for push notification approval
            # We need to poll for successful authentication
            
            # Retry logic for push notification approval
            max_retries = 12  # Total ~60 seconds
            retry_delay = 5   # 5 seconds between retries
            
            for attempt in range(max_retries):
                try:
                    logger.info(f"Verifying login (attempt {attempt + 1}/{max_retries})...")
                    
                    # Try to fetch account profile to verify login
                    test_profile = rh.load_account_profile()
                    
                    if test_profile and isinstance(test_profile, dict) and test_profile.get('url'):
                        # Login successful!
                        self.is_authenticated = True
                        self.session_active = True
                        
                        # Store the authentication token for future use
                        if self.account:
                            try:
                                # Store authentication metadata with expiration time
                                # We don't need to store the actual token since robin-stocks
                                # persists it to disk in ~/.tokens/robinhood.pickle
                                from core.encryption import CredentialEncryption
                                encryption = CredentialEncryption()
                                token_data = {'authenticated': True, 'username': username}
                                self.account.auth_token_encrypted = encryption.encrypt(token_data)
                                self.account.token_expires_at = timezone.now() + timedelta(hours=24)
                                self.account.save()
                                logger.info(f"Stored authentication metadata for account {self.account.account_number}")
                            except Exception as e:
                                logger.warning(f"Failed to store token metadata: {str(e)}, continuing anyway")
                        
                        logger.info(
                            f"Robinhood login successful after {attempt + 1} attempts: {username}",
                            extra={'username': username}
                        )
                        
                        return {
                            'success': True,
                            'message': f'Authentication successful (verified in {(attempt + 1) * retry_delay}s)',
                            'access_token': 'session_active',
                            'detail': 'Logged in - push notification approved or MFA code accepted',
                            'attempts': attempt + 1
                        }
                
                except Exception as e:
                    # If this is the last attempt, raise the error
                    if attempt == max_retries - 1:
                        logger.error(f"All {max_retries} verification attempts failed")
                        raise RobinhoodAPIError(
                            f"Authentication timeout: Waited {max_retries * retry_delay}s but login not verified. "
                            f"Please approve the push notification in your Robinhood app or check your credentials."
                        )
                    
                    # Otherwise, wait and retry
                    logger.info(f"Verification attempt {attempt + 1} failed, waiting {retry_delay}s...")
                    time.sleep(retry_delay)
            
            # Should not reach here due to the raise in the loop
            raise RobinhoodAPIError("Authentication verification loop completed without success")
        
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
        if not self.is_authenticated:
            raise RobinhoodAPIError("Not authenticated. Call authenticate() first.")
        
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
        if not self.is_authenticated:
            raise RobinhoodAPIError("Not authenticated. Call authenticate() first.")
        
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
        if not self.is_authenticated:
            raise RobinhoodAPIError("Not authenticated. Call authenticate() first.")
        
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
        if not self.is_authenticated:
            raise RobinhoodAPIError("Not authenticated. Call authenticate() first.")
        
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
        if not self.is_authenticated:
            raise RobinhoodAPIError("Not authenticated. Call authenticate() first.")
        
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
        if not self.is_authenticated:
            raise RobinhoodAPIError("Not authenticated. Call authenticate() first.")
        
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
