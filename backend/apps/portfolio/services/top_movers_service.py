"""
Top Movers Service - Analyze holdings to find top winners and losers.
Identifies best and worst performing positions for the current trading day.
"""
from decimal import Decimal
import logging
from typing import Dict, Any, List, Optional

from apps.portfolio.models import Portfolio, Holding
from apps.robinhood.client import RobinhoodClient

logger = logging.getLogger('apps')


class TopMoversService:
    """
    Service for analyzing top movers in portfolio.
    
    Handles:
    - Top holdings by portfolio allocation %
    - Top winners/losers by percentage change (today)
    - Top winners/losers by dollar change (today)
    """
    
    def __init__(self, user, robinhood_client: RobinhoodClient):
        """
        Initialize top movers service.
        
        Args:
            user: Django User instance
            robinhood_client: Authenticated RobinhoodClient instance
        """
        self.user = user
        self.rh_client = robinhood_client
    
    def get_top_holding(self, portfolio: Portfolio) -> Optional[Dict[str, Any]]:
        """
        Get the largest holding by market value (concentration risk).
        
        Args:
            portfolio: Portfolio instance
            
        Returns:
            Dict with top holding info or None if no holdings
        """
        try:
            # Get holdings sorted by market value (descending)
            holdings = Holding.get_user_holdings(self.user.id, active_only=True)
            
            if not holdings:
                return None
            
            # Sort by market value
            sorted_holdings = sorted(
                holdings,
                key=lambda h: float(h.market_value),
                reverse=True
            )
            
            top_holding = sorted_holdings[0]
            portfolio_value = float(portfolio.total_value)
            
            # Calculate allocation percentage
            allocation_percent = (float(top_holding.market_value) / portfolio_value * 100) if portfolio_value > 0 else 0
            
            return {
                'symbol': top_holding.symbol,
                'company_name': top_holding.company_name or top_holding.symbol,
                'market_value': float(top_holding.market_value),
                'allocation_percent': allocation_percent,
                'quantity': float(top_holding.quantity),
                'asset_type': top_holding.asset_type
            }
        
        except Exception as e:
            logger.error(f"Error getting top holding for user {self.user.id}: {str(e)}", exc_info=True)
            return None
    
    def get_holdings_analytics(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Get holdings count and breakdown.
        
        Args:
            portfolio: Portfolio instance
            
        Returns:
            Dict with holdings analytics
        """
        try:
            holdings = Holding.get_user_holdings(self.user.id, active_only=True)
            
            # Count by asset type
            stocks_count = sum(1 for h in holdings if h.asset_type == 'stock')
            options_count = sum(1 for h in holdings if h.asset_type == 'option')
            crypto_count = sum(1 for h in holdings if h.asset_type == 'crypto')
            
            return {
                'total_holdings': len(holdings),
                'stocks_count': stocks_count,
                'options_count': options_count,
                'crypto_count': crypto_count
            }
        
        except Exception as e:
            logger.error(f"Error getting holdings analytics: {str(e)}", exc_info=True)
            return {
                'total_holdings': 0,
                'stocks_count': 0,
                'options_count': 0,
                'crypto_count': 0
            }
    
    def get_top_movers(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Get top winners and losers by both percentage and dollar amount.
        
        Args:
            portfolio: Portfolio instance
            
        Returns:
            Dict with top movers data
        """
        try:
            holdings = list(Holding.get_user_holdings(self.user.id, active_only=True))
            
            if not holdings:
                return self._empty_movers_response()
            
            # Calculate today's changes for all holdings
            holdings_with_changes = []
            
            for holding in holdings:
                try:
                    # Get quote with previous_close
                    quote = self.rh_client.get_stock_quote(holding.symbol)
                    
                    if not quote:
                        continue
                    
                    previous_close = Decimal(str(quote.get('previous_close', '0')))
                    current_price = Decimal(str(quote.get('last_trade_price', '0')))
                    
                    if previous_close <= 0 or current_price <= 0:
                        continue
                    
                    # Calculate changes
                    price_change = current_price - previous_close
                    percent_change = (price_change / previous_close * Decimal('100'))
                    dollar_change = price_change * holding.quantity
                    
                    holdings_with_changes.append({
                        'symbol': holding.symbol,
                        'company_name': holding.company_name or holding.symbol,
                        'asset_type': holding.asset_type,
                        'quantity': float(holding.quantity),
                        'current_price': float(current_price),
                        'previous_close': float(previous_close),
                        'price_change': float(price_change),
                        'percent_change': float(percent_change),
                        'dollar_change': float(dollar_change),
                        'market_value': float(holding.market_value)
                    })
                
                except Exception as e:
                    logger.warning(f"Error calculating changes for {holding.symbol}: {str(e)}")
                    continue
            
            if not holdings_with_changes:
                return self._empty_movers_response()
            
            # Sort and find top movers
            top_winner_percent = self._get_top_mover(holdings_with_changes, 'percent_change', reverse=True)
            top_loser_percent = self._get_top_mover(holdings_with_changes, 'percent_change', reverse=False)
            top_winner_dollar = self._get_top_mover(holdings_with_changes, 'dollar_change', reverse=True)
            top_loser_dollar = self._get_top_mover(holdings_with_changes, 'dollar_change', reverse=False)
            
            logger.info(
                f"Top movers calculated for user {self.user.id}: "
                f"Processed {len(holdings_with_changes)}/{len(holdings)} holdings"
            )
            
            return {
                'top_winner_percent': top_winner_percent,
                'top_loser_percent': top_loser_percent,
                'top_winner_dollar': top_winner_dollar,
                'top_loser_dollar': top_loser_dollar,
                'holdings_analyzed': len(holdings_with_changes)
            }
        
        except Exception as e:
            logger.error(f"Error getting top movers for user {self.user.id}: {str(e)}", exc_info=True)
            return self._empty_movers_response()
    
    def _get_top_mover(self, holdings: List[Dict], sort_key: str, reverse: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get top mover from list of holdings by specified sort key.
        
        Args:
            holdings: List of holdings with changes
            sort_key: Key to sort by ('percent_change' or 'dollar_change')
            reverse: True for highest (winners), False for lowest (losers)
            
        Returns:
            Dict with top mover info or None
        """
        if not holdings:
            return None
        
        sorted_holdings = sorted(holdings, key=lambda h: h[sort_key], reverse=reverse)
        top = sorted_holdings[0]
        
        return {
            'symbol': top['symbol'],
            'company_name': top['company_name'],
            'asset_type': top['asset_type'],
            'current_price': top['current_price'],
            'previous_close': top['previous_close'],
            'price_change': top['price_change'],
            'percent_change': top['percent_change'],
            'dollar_change': top['dollar_change'],
            'market_value': top['market_value'],
            'quantity': top['quantity']
        }
    
    def _empty_movers_response(self) -> Dict[str, Any]:
        """
        Return empty response when no movers data available.
        
        Returns:
            Dict with None values
        """
        return {
            'top_winner_percent': None,
            'top_loser_percent': None,
            'top_winner_dollar': None,
            'top_loser_dollar': None,
            'holdings_analyzed': 0
        }
    
    def get_complete_analytics(self, portfolio: Portfolio) -> Dict[str, Any]:
        """
        Get complete holdings analytics overview.
        
        Args:
            portfolio: Portfolio instance
            
        Returns:
            Dict formatted for API response with all analytics
        """
        top_holding = self.get_top_holding(portfolio)
        holdings_analytics = self.get_holdings_analytics(portfolio)
        top_movers = self.get_top_movers(portfolio)
        
        return {
            # Holdings count and breakdown
            'total_holdings': holdings_analytics['total_holdings'],
            'stocks_count': holdings_analytics['stocks_count'],
            'options_count': holdings_analytics['options_count'],
            'crypto_count': holdings_analytics['crypto_count'],
            
            # Top holding (concentration)
            'top_holding': top_holding,
            
            # Top movers
            'top_winner_percent': top_movers['top_winner_percent'],
            'top_loser_percent': top_movers['top_loser_percent'],
            'top_winner_dollar': top_movers['top_winner_dollar'],
            'top_loser_dollar': top_movers['top_loser_dollar'],
            
            # Metadata
            'holdings_analyzed': top_movers['holdings_analyzed']
        }
