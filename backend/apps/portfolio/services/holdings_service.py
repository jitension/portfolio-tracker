"""
Holdings Service - Business logic for holdings management.
Handles individual position tracking and updates.
"""
from decimal import Decimal
import logging
from typing import Dict, Any, List, Optional
from django.core.cache import cache
from django.utils import timezone

from apps.portfolio.models import Holding, Portfolio
from apps.robinhood.models import RobinhoodAccount
from apps.robinhood.client import RobinhoodClient
from core.exceptions import PortfolioSyncError

logger = logging.getLogger('apps')


class HoldingsService:
    """
    Service class for managing holdings data.
    
    Handles:
    - Fetching holdings from Robinhood
    - Parsing position data
    - Updating MongoDB documents
    - Cache management
    """
    
    CACHE_TIMEOUT = 900  # 15 minutes
    
    def __init__(self, user, robinhood_account: Optional[RobinhoodAccount] = None):
        """
        Initialize holdings service.
        
        Args:
            user: Django User instance
            robinhood_account: RobinhoodAccount instance (optional)
        """
        self.user = user
        self.robinhood_account = robinhood_account
        
        # Get or set default Robinhood account
        if not self.robinhood_account:
            accounts = RobinhoodAccount.get_user_accounts(user)
            if accounts:
                self.robinhood_account = accounts.first()
            else:
                raise ValueError(f"No Robinhood account found for user {user.id}")
        
        self.rh_client = RobinhoodClient(self.robinhood_account)
    
    def get_holdings(self, use_cache=True) -> List[Dict[str, Any]]:
        """
        Get all holdings with caching.
        
        Args:
            use_cache: Whether to use Redis cache
            
        Returns:
            List of holding dictionaries
        """
        cache_key = f'holdings_list_{self.user.id}'
        
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Holdings cache hit for user {self.user.id}")
                return cached_data
        
        # Get holdings from MongoDB
        holdings = Holding.get_user_holdings(self.user.id, active_only=True)
        
        # Convert to list of dicts
        holdings_list = []
        for holding in holdings:
            holdings_list.append(self._holding_to_dict(holding))
        
        # Cache the result
        if use_cache:
            cache.set(cache_key, holdings_list, self.CACHE_TIMEOUT)
            logger.debug(f"Holdings cached for user {self.user.id}")
        
        return holdings_list
    
    def sync_holdings_data(self) -> Dict[str, Any]:
        """
        Sync holdings data from Robinhood.
        
        This method:
        1. Fetches stock positions from Robinhood
        2. Updates/creates holdings in MongoDB
        3. Marks closed positions as inactive
        4. Updates portfolio totals
        
        Returns:
            Dictionary with sync results
            
        Raises:
            PortfolioSyncError: If sync fails
        """
        logger.info(
            f"Starting holdings sync for user {self.user.id}",
            extra={'user_id': self.user.id}
        )
        
        try:
            # Fetch stock positions from Robinhood (using cached session)
            rh_positions = self.rh_client.get_stock_positions()
            
            if rh_positions is None:
                raise PortfolioSyncError("No positions data returned from Robinhood")
            
            # Track symbols we've seen
            current_symbols = set()
            
            # Process each position
            holdings_created = 0
            holdings_updated = 0
            
            for rh_position in rh_positions:
                # Skip zero quantity positions
                quantity = float(rh_position.get('quantity', 0))
                if quantity == 0:
                    continue
                
                # Parse position data
                holding_data = self._parse_stock_position(rh_position)
                symbol = holding_data['symbol']
                current_symbols.add(symbol)
                
                # Get or create holding
                existing_holding = Holding.get_holding_by_symbol(
                    user_id=self.user.id,
                    symbol=symbol,
                    asset_type='stock'
                )
                
                if existing_holding:
                    # Update existing holding
                    existing_holding.update_from_data(holding_data)
                    holdings_updated += 1
                else:
                    # Create new holding
                    holding = Holding(
                        user_id=self.user.id,
                        robinhood_account_id=self.robinhood_account.id,
                        asset_type='stock',
                        **holding_data
                    )
                    holding.calculate_pl()
                    holding.save()
                    holdings_created += 1
            
            # Mark closed positions (symbols not in current positions)
            all_holdings = Holding.get_user_holdings(self.user.id, active_only=True)
            for holding in all_holdings:
                if holding.symbol not in current_symbols and holding.asset_type == 'stock':
                    holding.close_position()
            
            # Update portfolio totals
            self._update_portfolio_totals()
            
            # Invalidate cache
            self._invalidate_cache()
            
            logger.info(
                f"Holdings sync completed for user {self.user.id}",
                extra={
                    'user_id': self.user.id,
                    'holdings_created': holdings_created,
                    'holdings_updated': holdings_updated,
                    'total_holdings': holdings_created + holdings_updated
                }
            )
            
            return {
                'status': 'success',
                'holdings_created': holdings_created,
                'holdings_updated': holdings_updated,
                'total_holdings': holdings_created + holdings_updated,
                'synced_at': timezone.now().isoformat()
            }
            
        except Exception as e:
            logger.error(
                f"Holdings sync failed for user {self.user.id}: {str(e)}",
                extra={'user_id': self.user.id},
                exc_info=True
            )
            raise PortfolioSyncError(f"Holdings sync failed: {str(e)}") from e
    
    def _parse_stock_position(self, rh_position: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Robinhood stock position into our format.
        
        Args:
            rh_position: Raw position data from robin-stocks
            
        Returns:
            Dictionary with parsed holding data
        """
        try:
            # Extract instrument URL to get stock info
            instrument_url = rh_position.get('instrument')
            
            # Get stock quote for current price
            # Note: robin-stocks returns this in the position data
            symbol = rh_position.get('symbol', '').upper()
            
            # Parse quantities and prices
            quantity = Decimal(str(rh_position.get('quantity', '0')))
            average_buy_price = Decimal(str(rh_position.get('average_buy_price', '0')))
            
            # Get current price from instrument data
            # robin-stocks should provide this
            current_price = Decimal(str(rh_position.get('current_price', '0')))
            
            # If current price not in position, fetch it
            if current_price == 0 and symbol:
                try:
                    quote_data = self.rh_client.get_stock_quote(symbol)
                    if quote_data:
                        current_price = Decimal(str(quote_data.get('last_trade_price', '0')))
                except Exception as e:
                    logger.warning(
                        f"Failed to fetch quote for {symbol}: {str(e)}",
                        extra={'user_id': self.user.id, 'symbol': symbol}
                    )
            
            # Calculate market value
            market_value = quantity * current_price
            
            # Get company name if available
            company_name = rh_position.get('name', symbol)
            
            holding_data = {
                'symbol': symbol,
                'quantity': quantity,
                'average_cost': average_buy_price,
                'current_price': current_price,
                'market_value': market_value,
                'company_name': company_name,
                'is_active': True,
            }
            
            logger.debug(
                f"Parsed stock position: {symbol}",
                extra={'user_id': self.user.id, 'symbol': symbol}
            )
            
            return holding_data
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                f"Error parsing stock position: {str(e)}",
                extra={'user_id': self.user.id, 'raw_position': rh_position},
                exc_info=True
            )
            raise PortfolioSyncError(f"Failed to parse stock position: {str(e)}") from e
    
    def _update_portfolio_totals(self):
        """
        Update portfolio document with aggregated holdings data.
        
        Calculates:
        - Total stocks value
        - Holdings counts
        - Updates Portfolio document
        """
        portfolio = Portfolio.get_or_create_for_user(
            user_id=self.user.id,
            account_id=self.robinhood_account.id
        )
        
        # Get all active holdings
        holdings = Holding.get_user_holdings(self.user.id, active_only=True)
        
        # Calculate totals
        stocks_value = Decimal('0')
        options_value = Decimal('0')
        crypto_value = Decimal('0')
        
        stocks_count = 0
        options_count = 0
        crypto_count = 0
        
        total_pl = Decimal('0')
        
        for holding in holdings:
            if holding.asset_type == 'stock':
                stocks_value += holding.market_value
                stocks_count += 1
            elif holding.asset_type == 'option':
                options_value += holding.market_value
                options_count += 1
            elif holding.asset_type == 'crypto':
                crypto_value += holding.market_value
                crypto_count += 1
            
            total_pl += holding.total_pl
        
        # Calculate total P&L percentage
        total_cost_basis = stocks_value + options_value + crypto_value - total_pl
        total_pl_percent = (total_pl / total_cost_basis * 100) if total_cost_basis > 0 else Decimal('0')
        
        # Update portfolio
        portfolio.stocks_value = stocks_value
        portfolio.options_value = options_value
        portfolio.crypto_value = crypto_value
        portfolio.stocks_count = stocks_count
        portfolio.options_count = options_count
        portfolio.crypto_count = crypto_count
        portfolio.holdings_count = stocks_count + options_count + crypto_count
        portfolio.total_pl = total_pl
        portfolio.total_pl_percent = total_pl_percent
        
        # Update total equity if not set
        if portfolio.total_equity == 0:
            portfolio.total_equity = stocks_value + options_value + crypto_value
            portfolio.total_value = portfolio.total_equity + portfolio.cash
        
        portfolio.last_updated = timezone.now()
        portfolio.save()
        
        logger.info(
            f"Portfolio totals updated for user {self.user.id}",
            extra={
                'user_id': self.user.id,
                'stocks_value': float(stocks_value),
                'holdings_count': portfolio.holdings_count
            }
        )
    
    def _holding_to_dict(self, holding: Holding) -> Dict[str, Any]:
        """Convert Holding document to dictionary."""
        return {
            'id': str(holding.id),
            'symbol': holding.symbol,
            'asset_type': holding.asset_type,
            'quantity': float(holding.quantity),
            'average_cost': float(holding.average_cost),
            'current_price': float(holding.current_price),
            'market_value': float(holding.market_value),
            'total_pl': float(holding.total_pl),
            'total_pl_percent': float(holding.total_pl_percent),
            'daily_pl': float(holding.daily_pl),
            'daily_pl_percent': float(holding.daily_pl_percent),
            'company_name': holding.company_name,
            'sector': holding.sector,
            'last_updated': holding.last_updated.isoformat() if holding.last_updated else None,
        }
    
    def _invalidate_cache(self):
        """Invalidate all holdings-related caches for the user."""
        cache_keys = [
            f'holdings_list_{self.user.id}',
            f'portfolio_summary_{self.user.id}',
        ]
        
        for key in cache_keys:
            cache.delete(key)
            logger.debug(f"Invalidated cache: {key}")
    
    def get_holding_by_symbol(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific holding by symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            Holding dictionary or None
        """
        holding = Holding.get_holding_by_symbol(
            user_id=self.user.id,
            symbol=symbol.upper()
        )
        
        if holding:
            return self._holding_to_dict(holding)
        
        return None
    
    def get_holdings_by_asset_type(self, asset_type: str) -> List[Dict[str, Any]]:
        """
        Get holdings filtered by asset type.
        
        Args:
            asset_type: 'stock', 'option', or 'crypto'
            
        Returns:
            List of holding dictionaries
        """
        holdings = Holding.objects(
            user_id=self.user.id,
            asset_type=asset_type,
            is_active=True
        )
        
        return [self._holding_to_dict(h) for h in holdings]
