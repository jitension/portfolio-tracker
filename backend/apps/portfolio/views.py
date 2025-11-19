"""
Django REST Framework views for Portfolio app.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
import logging

from .serializers import (
    PortfolioSerializer,
    HoldingSerializer,
    PortfolioSnapshotSerializer,
    SyncPortfolioSerializer,
    SyncResponseSerializer,
    InvestmentOverviewSerializer,
    PnLMetricsSerializer,
    HoldingsAnalyticsSerializer,
    HistoricalDataPointSerializer,
    AllocationDataSerializer,
)
from .services import PortfolioService, HoldingsService
from .services.margin_calculation_service import MarginCalculationService
from .services.pnl_calculation_service import PnLCalculationService
from .services.top_movers_service import TopMoversService
from .models import Portfolio, PortfolioSnapshot, Holding
from apps.robinhood.client import RobinhoodClient
from core.exceptions import PortfolioSyncError

logger = logging.getLogger('apps')


class PortfolioViewSet(viewsets.ViewSet):
    """
    ViewSet for portfolio management.
    
    Provides endpoints for:
    - Getting portfolio summary
    - Getting holdings list
    - Getting specific holding details
    - Syncing data from Robinhood
    - Getting historical performance
    """
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'], url_path='summary')
    def summary(self, request):
        """
        Get portfolio summary.
        
        Returns:
            Portfolio summary with total value, P&L, and breakdowns
        """
        try:
            service = PortfolioService(request.user)
            summary_data = service.get_portfolio_summary()
            
            serializer = PortfolioSerializer(data=summary_data)
            serializer.is_valid(raise_exception=True)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
        
        except ValueError as e:
            logger.warning(f"Portfolio summary error: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'NO_ACCOUNT',
                    'message': str(e)
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Portfolio summary error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to fetch portfolio summary'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='holdings')
    def holdings(self, request):
        """
        Get all holdings.
        
        Returns:
            List of all active holdings (stocks, options, crypto)
        """
        try:
            service = HoldingsService(request.user)
            holdings_data = service.get_holdings()
            
            serializer = HoldingSerializer(data=holdings_data, many=True)
            serializer.is_valid(raise_exception=True)
            
            return Response({
                'success': True,
                'data': {
                    'holdings': serializer.data,
                    'count': len(serializer.data)
                }
            })
        
        except ValueError as e:
            logger.warning(f"Holdings error: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'NO_ACCOUNT',
                    'message': str(e)
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Holdings error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to fetch holdings'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='holdings/(?P<symbol>[^/.]+)')
    def holding_detail(self, request, symbol=None):
        """
        Get specific holding by symbol.
        
        Args:
            symbol: Stock ticker symbol
            
        Returns:
            Holding details for the specified symbol
        """
        try:
            service = HoldingsService(request.user)
            holding_data = service.get_holding_by_symbol(symbol)
            
            if not holding_data:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NOT_FOUND',
                        'message': f'No holding found for symbol {symbol}'
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            serializer = HoldingSerializer(data=holding_data)
            serializer.is_valid(raise_exception=True)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
        
        except Exception as e:
            logger.error(f"Holding detail error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': f'Failed to fetch holding for {symbol}'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['post'], url_path='sync')
    def sync(self, request):
        """
        Sync portfolio data from Robinhood.
        
        This endpoint triggers a background job to:
        1. Fetch portfolio summary from Robinhood
        2. Fetch all holdings
        3. Update MongoDB
        4. Create snapshot
        
        Returns:
            Sync status and updated portfolio data
        """
        try:
            # Validate request data
            serializer = SyncPortfolioSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            
            # Initialize services
            portfolio_service = PortfolioService(request.user)
            holdings_service = HoldingsService(request.user)
            
            # Sync portfolio summary
            logger.info(f"Starting portfolio sync for user {request.user.id}")
            portfolio_result = portfolio_service.sync_portfolio_data()
            
            # Sync holdings
            logger.info(f"Starting holdings sync for user {request.user.id}")
            holdings_result = holdings_service.sync_holdings_data()
            
            # Combine results
            response_data = {
                'status': 'success',
                'message': 'Portfolio synced successfully',
                'synced_at': portfolio_result['synced_at'],
                'portfolio': portfolio_result['portfolio'],
                'holdings_created': holdings_result['holdings_created'],
                'holdings_updated': holdings_result['holdings_updated'],
                'total_holdings': holdings_result['total_holdings'],
            }
            
            response_serializer = SyncResponseSerializer(data=response_data)
            response_serializer.is_valid(raise_exception=True)
            
            return Response({
                'success': True,
                'data': response_serializer.data
            })
        
        except PortfolioSyncError as e:
            logger.error(f"Portfolio sync error: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'SYNC_ERROR',
                    'message': str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except ValueError as e:
            logger.warning(f"Sync validation error: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'NO_ACCOUNT',
                    'message': str(e)
                }
            }, status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            logger.error(f"Sync error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to sync portfolio data'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='performance')
    def performance(self, request):
        """
        Get historical portfolio performance.
        
        Query Parameters:
            days: Number of days to retrieve (default: 30)
            
        Returns:
            List of historical snapshots with performance data
        """
        try:
            days = int(request.query_params.get('days', 30))
            
            # Limit days to reasonable range
            if days < 1:
                days = 1
            elif days > 365:
                days = 365
            
            service = PortfolioService(request.user)
            performance_data = service.get_historical_performance(days=days)
            
            serializer = PortfolioSnapshotSerializer(data=performance_data, many=True)
            serializer.is_valid(raise_exception=True)
            
            return Response({
                'success': True,
                'data': {
                    'snapshots': serializer.data,
                    'count': len(serializer.data),
                    'days': days
                }
            })
        
        except ValueError as e:
            logger.warning(f"Performance error: {str(e)}")
            return Response({
                'success': False,
                'error': {
                    'code': 'INVALID_PARAMETER',
                    'message': str(e)
                }
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Performance error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to fetch performance data'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # NEW ENHANCED DASHBOARD ENDPOINTS
    
    @action(detail=False, methods=['get'], url_path='investment-overview')
    def investment_overview(self, request):
        """
        Get investment overview with margin and leverage metrics.
        
        Returns:
            Investment metrics including cash invested, margin, and leverage
        """
        try:
            # Get portfolio and robinhood client
            from apps.robinhood.models import RobinhoodAccount
            
            rh_account = RobinhoodAccount.get_user_accounts(request.user).first()
            if not rh_account:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NO_ACCOUNT',
                        'message': 'No Robinhood account found'
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            portfolio = Portfolio.get_or_create_for_user(
                user_id=request.user.id,
                account_id=rh_account.id
            )
            
            # Initialize services
            rh_client = RobinhoodClient(rh_account)
            # Session already exists from account linking - no need to re-authenticate
            
            margin_service = MarginCalculationService(request.user, rh_client)
            
            # Get margin overview
            overview_data = margin_service.get_margin_overview(portfolio)
            
            # Don't logout - keep session active
            
            serializer = InvestmentOverviewSerializer(data=overview_data)
            serializer.is_valid(raise_exception=True)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
        
        except Exception as e:
            logger.error(f"Investment overview error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to fetch investment overview'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='pnl-metrics')
    def pnl_metrics(self, request):
        """
        Get P&L metrics (Year-to-Date and today).
        
        Returns:
            P&L metrics including YTD and today's performance
        """
        try:
            # Get portfolio and robinhood client
            from apps.robinhood.models import RobinhoodAccount
            
            rh_account = RobinhoodAccount.get_user_accounts(request.user).first()
            if not rh_account:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NO_ACCOUNT',
                        'message': 'No Robinhood account found'
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            portfolio = Portfolio.get_or_create_for_user(
                user_id=request.user.id,
                account_id=rh_account.id
            )
            
            # Initialize services
            rh_client = RobinhoodClient(rh_account)
            # Session already exists from account linking - no need to re-authenticate
            
            pnl_service = PnLCalculationService(request.user, rh_client)
            
            # Get P&L overview
            pnl_data = pnl_service.get_pnl_overview(portfolio)
            
            # Don't logout - keep session active
            
            serializer = PnLMetricsSerializer(data=pnl_data)
            serializer.is_valid(raise_exception=True)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
        
        except Exception as e:
            logger.error(f"P&L metrics error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to fetch P&L metrics'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='holdings-analytics')
    def holdings_analytics(self, request):
        """
        Get holdings analytics including top movers and concentration.
        
        Returns:
            Holdings analytics with top winners/losers and concentration risk
        """
        try:
            # Get portfolio and robinhood client
            from apps.robinhood.models import RobinhoodAccount
            
            rh_account = RobinhoodAccount.get_user_accounts(request.user).first()
            if not rh_account:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NO_ACCOUNT',
                        'message': 'No Robinhood account found'
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            portfolio = Portfolio.get_or_create_for_user(
                user_id=request.user.id,
                account_id=rh_account.id
            )
            
            # Initialize services
            rh_client = RobinhoodClient(rh_account)
            # Session already exists from account linking - no need to re-authenticate
            
            top_movers_service = TopMoversService(request.user, rh_client)
            
            # Get complete analytics
            analytics_data = top_movers_service.get_complete_analytics(portfolio)
            
            # Don't logout - keep session active
            
            serializer = HoldingsAnalyticsSerializer(data=analytics_data)
            serializer.is_valid(raise_exception=True)
            
            return Response({
                'success': True,
                'data': serializer.data
            })
        
        except Exception as e:
            logger.error(f"Holdings analytics error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to fetch holdings analytics'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='historical')
    def historical(self, request):
        """
        Get historical portfolio data for charts.
        
        Query Parameters:
            period: Time period (1D, 1W, 1M, 1Y, YTD, All) - default: 1M
            
        Returns:
            List of historical data points for chart
        """
        try:
            from datetime import datetime, timedelta
            from django.utils import timezone
            
            period = request.query_params.get('period', '1M').upper()
            
            # Calculate date range based on period
            now = timezone.now()
            if period == '1D':
                start_date = now - timedelta(days=1)
            elif period == '1W':
                start_date = now - timedelta(days=7)
            elif period == '1M':
                start_date = now - timedelta(days=30)
            elif period == '1Y':
                start_date = now - timedelta(days=365)
            elif period == 'YTD':
                start_date = datetime(now.year, 1, 1, tzinfo=now.tzinfo)
            elif period == 'ALL':
                start_date = None  # Get all data
            else:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'INVALID_PARAMETER',
                        'message': f'Invalid period: {period}. Use 1D, 1W, 1M, 1Y, YTD, or All'
                    }
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Query snapshots
            query = {'user_id': request.user.id}
            if start_date:
                query['timestamp__gte'] = start_date
            
            snapshots = PortfolioSnapshot.objects(**query).order_by('timestamp')
            
            # Format data for chart
            historical_data = []
            for snapshot in snapshots:
                historical_data.append({
                    'timestamp': snapshot.timestamp,
                    'value': float(snapshot.total_value),
                    'change': float(snapshot.daily_pl),
                    'change_percent': float(snapshot.daily_pl_percent)
                })
            
            serializer = HistoricalDataPointSerializer(data=historical_data, many=True)
            serializer.is_valid(raise_exception=True)
            
            return Response({
                'success': True,
                'data': {
                    'period': period,
                    'data_points': serializer.data,
                    'count': len(serializer.data)
                }
            })
        
        except Exception as e:
            logger.error(f"Historical data error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to fetch historical data'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'], url_path='allocation')
    def allocation(self, request):
        """
        Get portfolio allocation data for pie chart.
        
        Returns:
            List of holdings with allocation percentages
        """
        try:
            from apps.robinhood.models import RobinhoodAccount
            
            rh_account = RobinhoodAccount.get_user_accounts(request.user).first()
            if not rh_account:
                return Response({
                    'success': False,
                    'error': {
                        'code': 'NO_ACCOUNT',
                        'message': 'No Robinhood account found'
                    }
                }, status=status.HTTP_404_NOT_FOUND)
            
            portfolio = Portfolio.get_or_create_for_user(
                user_id=request.user.id,
                account_id=rh_account.id
            )
            
            # Get all holdings
            holdings = Holding.get_user_holdings(request.user.id, active_only=True)
            
            portfolio_value = float(portfolio.total_value)
            
            # Format allocation data
            allocation_data = []
            for holding in holdings:
                market_value = float(holding.market_value)
                allocation_percent = (market_value / portfolio_value * 100) if portfolio_value > 0 else 0
                
                allocation_data.append({
                    'symbol': holding.symbol,
                    'company_name': holding.company_name or holding.symbol,
                    'asset_type': holding.asset_type,
                    'market_value': market_value,
                    'allocation_percent': allocation_percent,
                    'quantity': float(holding.quantity)
                })
            
            # Sort by allocation percentage (descending)
            allocation_data.sort(key=lambda x: x['allocation_percent'], reverse=True)
            
            serializer = AllocationDataSerializer(data=allocation_data, many=True)
            serializer.is_valid(raise_exception=True)
            
            return Response({
                'success': True,
                'data': {
                    'allocations': serializer.data,
                    'count': len(serializer.data)
                }
            })
        
        except Exception as e:
            logger.error(f"Allocation data error: {str(e)}", exc_info=True)
            return Response({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Failed to fetch allocation data'
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
