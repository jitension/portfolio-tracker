"""
P&L Calculation Service - Calculate Year-to-Date and Today's P&L.
Handles profit/loss calculations for different time periods.
"""
from decimal import Decimal
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from django.utils import timezone

from apps.portfolio.models import Portfolio, PortfolioSnapshot, Holding
from apps.robinhood.client import RobinhoodClient
from core.exceptions import PortfolioSyncError

logger = logging.getLogger('apps')


class PnLCalculationService:
    """
    Service for calculating profit and loss metrics.
    
    Handles:
    - Year-to-Date (YTD) P&L - from Jan 1 to current date
    - Today's P&L - from previous close to current value
    """
    
    def __init__(self, user, robinhood_client: RobinhoodClient):
        """
        Initialize P&L calculation service.
        
        Args:
            user: Django User instance
            robinhood_client: Authenticated RobinhoodClient instance
        """
        self.user = user
        self.rh_client = robinhood_client
    
    def calculate_ytd_pnl(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Calculate Year-to-Date P&L (Jan 1 to current date).
        
        Args:
            portfolio: Portfolio instance
            
        Returns:
            Dict with YTD P&L metrics:
            {
                'ytd_pnl': Decimal,
                'ytd_pnl_percent': Decimal,
                'baseline_date': datetime,
                'baseline_value': Decimal,
                'has_baseline': bool
            }
        """
        try:
            current_value = portfolio.total_value
            current_year = timezone.now().year
            
            # Query for Jan 1 snapshot
            jan_1_start = datetime(current_year, 1, 1, 0, 0, 0)
            jan_1_end = datetime(current_year, 1, 2, 0, 0, 0)
            
            jan_1_snapshot = PortfolioSnapshot.objects(
                user_id=self.user.id,
                timestamp__gte=jan_1_start,
                timestamp__lt=jan_1_end
            ).order_by('-timestamp').first()
            
            if jan_1_snapshot:
                # Found Jan 1 baseline
                baseline_value = jan_1_snapshot.total_value
                baseline_date = jan_1_snapshot.timestamp
                
                ytd_pnl = current_value - baseline_value
                ytd_pnl_percent = (ytd_pnl / baseline_value * Decimal('100')) if baseline_value > 0 else Decimal('0')
                
                logger.info(
                    f"YTD P&L calculated for user {self.user.id}: "
                    f"${ytd_pnl} ({ytd_pnl_percent}%) from baseline ${baseline_value}"
                )
                
                return {
                    'ytd_pnl': ytd_pnl,
                    'ytd_pnl_percent': ytd_pnl_percent,
                    'baseline_date': baseline_date,
                    'baseline_value': baseline_value,
                    'has_baseline': True
                }
            
            # No Jan 1 snapshot - try to find earliest snapshot this year
            earliest_snapshot = PortfolioSnapshot.objects(
                user_id=self.user.id,
                timestamp__gte=jan_1_start
            ).order_by('timestamp').first()
            
            if earliest_snapshot:
                # Use earliest available snapshot
                baseline_value = earliest_snapshot.total_value
                baseline_date = earliest_snapshot.timestamp
                
                ytd_pnl = current_value - baseline_value
                ytd_pnl_percent = (ytd_pnl / baseline_value * Decimal('100')) if baseline_value > 0 else Decimal('0')
                
                logger.warning(
                    f"No Jan 1 snapshot for user {self.user.id}, "
                    f"using earliest snapshot from {baseline_date}"
                )
                
                return {
                    'ytd_pnl': ytd_pnl,
                    'ytd_pnl_percent': ytd_pnl_percent,
                    'baseline_date': baseline_date,
                    'baseline_value': baseline_value,
                    'has_baseline': True
                }
            
            # No snapshots this year
            logger.warning(f"No historical snapshots found for user {self.user.id} YTD calculation")
            return {
                'ytd_pnl': Decimal('0'),
                'ytd_pnl_percent': Decimal('0'),
                'baseline_date': None,
                'baseline_value': None,
                'has_baseline': False
            }
        
        except Exception as e:
            logger.error(
                f"Error calculating YTD P&L for user {self.user.id}: {str(e)}",
                exc_info=True
            )
            return {
                'ytd_pnl': Decimal('0'),
                'ytd_pnl_percent': Decimal('0'),
                'baseline_date': None,
                'baseline_value': None,
                'has_baseline': False
            }
    
    def calculate_today_pnl(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Calculate today's P&L using previous_close from quotes.
        
        Args:
            portfolio: Portfolio instance
            
        Returns:
            Dict with today's P&L metrics:
            {
                'today_pnl': Decimal,
                'today_pnl_percent': Decimal,
                'previous_close_value': Decimal,
                'is_market_open': bool
            }
        """
        try:
            current_value = portfolio.total_value
            
            # Get all active holdings
            holdings = Holding.get_user_holdings(self.user.id, active_only=True)
            
            if not holdings:
                logger.info(f"No holdings found for user {self.user.id}")
                return self._market_closed_response()
            
            # Calculate portfolio value at previous close
            previous_close_value = Decimal('0')
            symbols_processed = 0
            
            for holding in holdings:
                try:
                    # Get quote with previous_close
                    quote = self.rh_client.get_stock_quote(holding.symbol)
                    
                    if not quote:
                        logger.warning(f"No quote data for {holding.symbol}")
                        # Use current price as fallback
                        previous_close_value += holding.market_value
                        continue
                    
                    previous_close = Decimal(str(quote.get('previous_close', '0')))
                    quantity = holding.quantity
                    
                    if previous_close > 0:
                        # Calculate value at previous close
                        prev_value = previous_close * quantity
                        previous_close_value += prev_value
                        symbols_processed += 1
                    else:
                        # No previous_close available, use current value
                        previous_close_value += holding.market_value
                
                except Exception as e:
                    logger.warning(f"Error processing {holding.symbol}: {str(e)}")
                    # Use current value as fallback
                    previous_close_value += holding.market_value
            
            # Add cash to both values
            previous_close_value += portfolio.cash
            
            # Calculate today's P&L
            today_pnl = current_value - previous_close_value
            today_pnl_percent = (today_pnl / previous_close_value * Decimal('100')) if previous_close_value > 0 else Decimal('0')
            
            # Determine if market is open
            is_market_open = self._is_market_open()
            
            logger.info(
                f"Today's P&L calculated for user {self.user.id}: "
                f"${today_pnl} ({today_pnl_percent}%) from previous close ${previous_close_value}, "
                f"processed {symbols_processed} symbols"
            )
            
            return {
                'today_pnl': today_pnl,
                'today_pnl_percent': today_pnl_percent,
                'previous_close_value': previous_close_value,
                'is_market_open': is_market_open,
                'symbols_processed': symbols_processed
            }
        
        except Exception as e:
            logger.error(
                f"Error calculating today's P&L for user {self.user.id}: {str(e)}",
                exc_info=True
            )
            return self._market_closed_response()
    
    def _is_market_open(self) -> bool:
        """
        Check if market is currently open.
        Simplified check based on time (9:30 AM - 4:00 PM ET, Mon-Fri).
        
        Returns:
            True if market is open, False otherwise
        """
        try:
            from datetime import time
            import pytz
            
            # Get current time in ET
            et_tz = pytz.timezone('America/New_York')
            now_et = timezone.now().astimezone(et_tz)
            
            # Check if weekend
            if now_et.weekday() >= 5:  # Saturday = 5, Sunday = 6
                return False
            
            # Check if within market hours (9:30 AM - 4:00 PM ET)
            market_open = time(9, 30)
            market_close = time(16, 0)
            current_time = now_et.time()
            
            return market_open <= current_time <= market_close
        
        except Exception as e:
            logger.warning(f"Error checking market status: {str(e)}")
            return False
    
    def _market_closed_response(self) -> Dict[str, Any]:
        """
        Return default response for market closed state.
        
        Returns:
            Dict with zero P&L values
        """
        return {
            'today_pnl': Decimal('0'),
            'today_pnl_percent': Decimal('0'),
            'previous_close_value': Decimal('0'),
            'is_market_open': False,
            'symbols_processed': 0
        }
    
    def get_pnl_overview(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Get complete P&L overview (both YTD and today).
        
        Args:
            portfolio: Portfolio instance
            
        Returns:
            Dict formatted for API response
        """
        ytd_metrics = self.calculate_ytd_pnl(portfolio)
        today_metrics = self.calculate_today_pnl(portfolio)
        
        return {
            # YTD metrics
            'ytd_pnl': float(ytd_metrics['ytd_pnl']),
            'ytd_pnl_percent': float(ytd_metrics['ytd_pnl_percent']),
            'has_ytd_baseline': ytd_metrics['has_baseline'],
            'ytd_baseline_date': ytd_metrics['baseline_date'].isoformat() if ytd_metrics['baseline_date'] else None,
            
            # Today's metrics
            'today_pnl': float(today_metrics['today_pnl']),
            'today_pnl_percent': float(today_metrics['today_pnl_percent']),
            'is_market_open': today_metrics['is_market_open'],
            
            # Status messages
            'ytd_message': self._get_ytd_message(ytd_metrics),
            'today_message': self._get_today_message(today_metrics)
        }
    
    def _get_ytd_message(self, metrics: Dict[str, Any]) -> str:
        """Get descriptive message for YTD P&L."""
        if not metrics['has_baseline']:
            return "Insufficient historical data for YTD calculation"
        
        baseline_date = metrics['baseline_date']
        if baseline_date:
            return f"Since {baseline_date.strftime('%B %d, %Y')}"
        return "YTD performance"
    
    def _get_today_message(self, metrics: Dict[str, Any]) -> str:
        """Get descriptive message for today's P&L."""
        if not metrics['is_market_open']:
            return "Market closed - showing last known values"
        return "Current trading day performance"
