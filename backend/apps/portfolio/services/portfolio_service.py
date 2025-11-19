"""
Portfolio Service - Business logic for portfolio management.
Handles data synchronization from Robinhood to MongoDB.
"""
from decimal import Decimal
import logging
from typing import Dict, Any, Optional
from django.core.cache import cache
from django.utils import timezone

from apps.portfolio.models import Portfolio, PortfolioSnapshot
from apps.robinhood.models import RobinhoodAccount
from apps.robinhood.client import RobinhoodClient
from core.exceptions import PortfolioSyncError

logger = logging.getLogger('apps')


class PortfolioService:
    """
    Service class for managing portfolio data.
    
    Handles:
    - Fetching portfolio data from Robinhood
    - Calculating portfolio metrics
    - Updating MongoDB documents
    - Cache management
    """
    
    CACHE_TIMEOUT = 900  # 15 minutes
    
    def __init__(self, user, robinhood_account: Optional[RobinhoodAccount] = None):
        """
        Initialize portfolio service.
        
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
    
    def get_portfolio_summary(self, use_cache=True) -> Dict[str, Any]:
        """
        Get portfolio summary with caching.
        
        Args:
            use_cache: Whether to use Redis cache
            
        Returns:
            Dictionary with portfolio summary data
        """
        cache_key = f'portfolio_summary_{self.user.id}'
        
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Portfolio summary cache hit for user {self.user.id}")
                return cached_data
        
        # Get portfolio from MongoDB
        portfolio = Portfolio.get_or_create_for_user(
            user_id=self.user.id,
            account_id=self.robinhood_account.id
        )
        
        # Convert to dict
        summary = {
            'total_value': float(portfolio.total_value),
            'total_equity': float(portfolio.total_equity),
            'cash': float(portfolio.cash),
            'buying_power': float(portfolio.buying_power),
            'total_pl': float(portfolio.total_pl),
            'total_pl_percent': float(portfolio.total_pl_percent),
            'daily_pl': float(portfolio.daily_pl),
            'daily_pl_percent': float(portfolio.daily_pl_percent),
            'stocks_value': float(portfolio.stocks_value),
            'options_value': float(portfolio.options_value),
            'crypto_value': float(portfolio.crypto_value),
            'holdings_count': portfolio.holdings_count,
            'stocks_count': portfolio.stocks_count,
            'options_count': portfolio.options_count,
            'crypto_count': portfolio.crypto_count,
            'market_status': portfolio.market_status,
            'last_updated': portfolio.last_updated.isoformat() if portfolio.last_updated else None,
        }
        
        # Cache the result
        if use_cache:
            cache.set(cache_key, summary, self.CACHE_TIMEOUT)
            logger.debug(f"Portfolio summary cached for user {self.user.id}")
        
        return summary
    
    def sync_portfolio_data(self) -> Dict[str, Any]:
        """
        Sync portfolio data from Robinhood.
        
        This is the main sync method that:
        1. Authenticates with Robinhood
        2. Fetches portfolio data
        3. Updates MongoDB
        4. Invalidates cache
        5. Creates snapshot
        
        Returns:
            Dictionary with sync results
            
        Raises:
            PortfolioSyncError: If sync fails
        """
        logger.info(
            f"Starting portfolio sync for user {self.user.id}",
            extra={'user_id': self.user.id, 'account_id': str(self.robinhood_account.id)}
        )
        
        try:
            # Update sync status to pending
            self.robinhood_account.update_sync_status('pending')
            
            # Fetch portfolio data from Robinhood (using cached session)
            rh_portfolio_data = self.rh_client.get_portfolio()
            
            if not rh_portfolio_data:
                raise PortfolioSyncError("No portfolio data returned from Robinhood")
            
            # Parse and calculate portfolio metrics
            portfolio_data = self._parse_portfolio_data(rh_portfolio_data)
            
            # Update Portfolio document in MongoDB
            portfolio = Portfolio.get_or_create_for_user(
                user_id=self.user.id,
                account_id=self.robinhood_account.id
            )
            portfolio.update_values(portfolio_data)
            
            # Create snapshot
            PortfolioSnapshot.create_from_portfolio(portfolio, snapshot_type='sync')
            
            # Invalidate cache
            self._invalidate_cache()
            
            # Update sync status to success
            self.robinhood_account.update_sync_status('success')
            
            logger.info(
                f"Portfolio sync completed successfully for user {self.user.id}",
                extra={
                    'user_id': self.user.id,
                    'total_value': float(portfolio.total_value),
                    'holdings_count': portfolio.holdings_count
                }
            )
            
            return {
                'status': 'success',
                'synced_at': timezone.now().isoformat(),
                'portfolio': self.get_portfolio_summary(use_cache=False)
            }
            
        except Exception as e:
            logger.error(
                f"Portfolio sync failed for user {self.user.id}: {str(e)}",
                extra={'user_id': self.user.id},
                exc_info=True
            )
            
            # Update sync status to failed
            self.robinhood_account.update_sync_status('failed', error=str(e))
            
            raise PortfolioSyncError(f"Portfolio sync failed: {str(e)}") from e
    
    def _parse_portfolio_data(self, rh_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse Robinhood portfolio data into our format.
        
        Args:
            rh_data: Raw data from robin-stocks
            
        Returns:
            Dictionary with parsed portfolio data
        """
        try:
            # Extract values from Robinhood response
            # Note: Robinhood API returns strings, need to convert to Decimal
            # Handle None values explicitly before Decimal conversion
            equity_value = rh_data.get('equity') or '0'
            equity = Decimal(equity_value)
            
            # Handle extended_hours_equity which may be None
            extended_hours_value = rh_data.get('extended_hours_equity')
            extended_hours_equity = Decimal(extended_hours_value) if extended_hours_value is not None else equity
            
            # Use extended hours equity if market is closed
            total_equity = extended_hours_equity if extended_hours_equity else equity
            
            # Calculate market value (equity - previous close)
            # Handle equity_previous_close which may be None
            equity_previous_close_value = rh_data.get('equity_previous_close')
            equity_previous_close = Decimal(equity_previous_close_value) if equity_previous_close_value is not None else equity
            daily_pl = total_equity - equity_previous_close
            daily_pl_percent = (daily_pl / equity_previous_close * 100) if equity_previous_close > 0 else Decimal('0')
            
            # Total P&L calculation (would need initial investment data)
            # For now, we'll calculate based on current positions
            # This will be enhanced when we have transaction history
            total_pl = Decimal('0')
            total_pl_percent = Decimal('0')
            
            # Market status
            market_open = rh_data.get('market_value', None) is not None
            market_status = 'open' if market_open else 'closed'
            
            portfolio_data = {
                'total_value': total_equity,
                'total_equity': total_equity,
                'cash': Decimal('0'),  # Will be updated by HoldingsService
                'buying_power': Decimal('0'),  # Will be updated by HoldingsService
                'total_pl': total_pl,
                'total_pl_percent': total_pl_percent,
                'daily_pl': daily_pl,
                'daily_pl_percent': daily_pl_percent,
                'market_status': market_status,
                'last_updated': timezone.now(),
            }
            
            logger.debug(
                f"Parsed portfolio data for user {self.user.id}",
                extra={'user_id': self.user.id, 'portfolio_data': portfolio_data}
            )
            
            return portfolio_data
            
        except (KeyError, ValueError, TypeError) as e:
            logger.error(
                f"Error parsing portfolio data: {str(e)}",
                extra={'user_id': self.user.id, 'raw_data': rh_data},
                exc_info=True
            )
            raise PortfolioSyncError(f"Failed to parse portfolio data: {str(e)}") from e
    
    def _invalidate_cache(self):
        """Invalidate all portfolio-related caches for the user."""
        cache_keys = [
            f'portfolio_summary_{self.user.id}',
            f'holdings_list_{self.user.id}',
        ]
        
        for key in cache_keys:
            cache.delete(key)
            logger.debug(f"Invalidated cache: {key}")
    
    def create_snapshot(self, snapshot_type='manual') -> PortfolioSnapshot:
        """
        Create a portfolio snapshot.
        
        Args:
            snapshot_type: Type of snapshot ('daily', 'manual', 'sync')
            
        Returns:
            Created PortfolioSnapshot instance
        """
        portfolio = Portfolio.get_or_create_for_user(
            user_id=self.user.id,
            account_id=self.robinhood_account.id
        )
        
        snapshot = PortfolioSnapshot.create_from_portfolio(
            portfolio,
            snapshot_type=snapshot_type
        )
        
        logger.info(
            f"Portfolio snapshot created: {snapshot_type}",
            extra={
                'user_id': self.user.id,
                'snapshot_id': str(snapshot.id),
                'snapshot_type': snapshot_type
            }
        )
        
        return snapshot
    
    def get_historical_performance(self, days=30) -> list:
        """
        Get historical portfolio performance.
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of snapshot data dictionaries
        """
        snapshots = PortfolioSnapshot.get_user_snapshots(
            user_id=self.user.id,
            days=days
        )
        
        performance_data = []
        for snapshot in snapshots:
            performance_data.append({
                'timestamp': snapshot.timestamp.isoformat(),
                'total_value': float(snapshot.total_value),
                'total_pl': float(snapshot.total_pl),
                'total_pl_percent': float(snapshot.total_pl_percent),
                'daily_pl': float(snapshot.daily_pl),
                'daily_pl_percent': float(snapshot.daily_pl_percent),
            })
        
        return performance_data
    
    def calculate_portfolio_metrics(self) -> Dict[str, Any]:
        """
        Calculate advanced portfolio metrics.
        
        Returns:
            Dictionary with calculated metrics
            
        Note: This is a placeholder for future implementation
        of metrics like Sharpe ratio, volatility, etc.
        """
        # TODO: Implement advanced metrics calculation
        # - Volatility
        # - Sharpe Ratio
        # - Beta
        # - Maximum Drawdown
        
        return {
            'volatility': None,
            'sharpe_ratio': None,
            'beta': None,
            'max_drawdown': None,
        }
