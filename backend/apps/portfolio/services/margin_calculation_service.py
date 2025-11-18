"""
Margin Calculation Service - Calculate margin and leverage metrics.
Uses robin_stocks to fetch margin data and calculate investment metrics.
"""
from decimal import Decimal
import logging
from typing import Dict, Any, Optional

from apps.portfolio.models import Portfolio
from apps.robinhood.client import RobinhoodClient
from core.exceptions import PortfolioSyncError

logger = logging.getLogger('apps')


class MarginCalculationService:
    """
    Service for calculating margin and leverage metrics.
    
    Handles:
    - Cash invested (without margin)
    - Margin invested
    - Margin available
    - Leverage percentage
    """
    
    def __init__(self, user, robinhood_client: RobinhoodClient):
        """
        Initialize margin calculation service.
        
        Args:
            user: Django User instance
            robinhood_client: Authenticated RobinhoodClient instance
        """
        self.user = user
        self.rh_client = robinhood_client
    
    def calculate_margin_metrics(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Calculate all margin-related metrics for portfolio.
        
        Args:
            portfolio: Portfolio instance
            
        Returns:
            Dict with margin metrics:
            {
                'cash_invested': Decimal,
                'margin_invested': Decimal,
                'margin_available': Decimal,
                'leverage_percent': Decimal,
                'is_margin_account': bool
            }
        """
        try:
            # Fetch margin data from Robinhood
            margin_data = self.rh_client.get_margin_interest()
            
            if not margin_data:
                # No margin data - treat as cash account
                logger.info(f"No margin data for user {self.user.id}, treating as cash account")
                return self._cash_account_metrics(portfolio)
            
            # Check if margin account
            is_margin_account = margin_data.get('is_margin_account', False)
            
            if not is_margin_account:
                return self._cash_account_metrics(portfolio)
            
            # Calculate margin metrics
            margin_limit = Decimal(str(margin_data.get('margin_limit', 0)))
            unallocated_margin = Decimal(str(margin_data.get('unallocated_margin_cash', 0)))
            cash_balance = Decimal(str(margin_data.get('cash', 0)))
            
            # Margin invested = margin_limit - unallocated_margin
            margin_invested = margin_limit - unallocated_margin
            
            # Margin available = unallocated_margin
            margin_available = unallocated_margin
            
            # Cash invested = total portfolio value - margin invested
            total_value = portfolio.total_value
            cash_invested = total_value - margin_invested
            
            # Ensure cash_invested is not negative
            if cash_invested < 0:
                cash_invested = Decimal('0')
            
            # Calculate leverage percentage
            # Leverage = (Total Portfolio Value / Cash Invested) × 100
            if cash_invested > 0:
                leverage_percent = (total_value / cash_invested) * Decimal('100')
            else:
                # If no cash invested (all margin), set very high leverage
                leverage_percent = Decimal('999.9')
            
            logger.info(
                f"Margin metrics calculated for user {self.user.id}: "
                f"Cash: ${cash_invested}, Margin: ${margin_invested}, "
                f"Leverage: {leverage_percent}%"
            )
            
            return {
                'cash_invested': cash_invested,
                'margin_invested': margin_invested,
                'margin_available': margin_available,
                'leverage_percent': leverage_percent,
                'is_margin_account': True
            }
        
        except Exception as e:
            logger.error(
                f"Error calculating margin metrics for user {self.user.id}: {str(e)}",
                exc_info=True
            )
            # Return safe defaults on error
            return self._cash_account_metrics(portfolio)
    
    def _cash_account_metrics(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Return metrics for a cash account (no margin).
        
        Args:
            portfolio: Portfolio instance
            
        Returns:
            Dict with cash account metrics
        """
        return {
            'cash_invested': portfolio.total_value,
            'margin_invested': Decimal('0'),
            'margin_available': Decimal('0'),
            'leverage_percent': Decimal('100.0'),  # 100% = no leverage
            'is_margin_account': False
        }
    
    def get_margin_overview(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Get complete margin overview for display.
        
        Args:
            portfolio: Portfolio instance
            
        Returns:
            Dict formatted for API response
        """
        metrics = self.calculate_margin_metrics(portfolio)
        
        return {
            'cash_invested': float(metrics['cash_invested']),
            'margin_invested': float(metrics['margin_invested']),
            'total_invested': float(metrics['cash_invested'] + metrics['margin_invested']),
            'margin_available': float(metrics['margin_available']),
            'leverage_percent': float(metrics['leverage_percent']),
            'is_margin_account': metrics['is_margin_account'],
            'message': self._get_leverage_message(metrics['leverage_percent'])
        }
    
    def _get_leverage_message(self, leverage_percent: Decimal) -> str:
        """
        Get descriptive message based on leverage level.
        
        Args:
            leverage_percent: Leverage percentage
            
        Returns:
            Human-readable message
        """
        if leverage_percent <= 100:
            return "No leverage - cash account"
        elif leverage_percent <= 150:
            return "Moderate leverage"
        elif leverage_percent <= 200:
            return "High leverage"
        else:
            return "Very high leverage - increased risk"
