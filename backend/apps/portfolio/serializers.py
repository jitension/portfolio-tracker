"""
Django REST Framework serializers for Portfolio app.
"""
from rest_framework import serializers
from .models import Portfolio, Holding, PortfolioSnapshot


class PortfolioSerializer(serializers.Serializer):
    """Serializer for Portfolio summary data."""
    
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_equity = serializers.DecimalField(max_digits=12, decimal_places=2)
    cash = serializers.DecimalField(max_digits=12, decimal_places=2)
    buying_power = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pl = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pl_percent = serializers.DecimalField(max_digits=8, decimal_places=2)
    daily_pl = serializers.DecimalField(max_digits=12, decimal_places=2)
    daily_pl_percent = serializers.DecimalField(max_digits=8, decimal_places=2)
    stocks_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    options_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    crypto_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    holdings_count = serializers.IntegerField()
    stocks_count = serializers.IntegerField()
    options_count = serializers.IntegerField()
    crypto_count = serializers.IntegerField()
    market_status = serializers.CharField()
    last_updated = serializers.DateTimeField()


class HoldingSerializer(serializers.Serializer):
    """Serializer for individual holdings."""
    
    id = serializers.CharField()
    symbol = serializers.CharField(max_length=20)
    asset_type = serializers.ChoiceField(choices=['stock', 'option', 'crypto'])
    quantity = serializers.DecimalField(max_digits=16, decimal_places=8)
    average_cost = serializers.DecimalField(max_digits=12, decimal_places=2)
    current_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    market_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pl = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pl_percent = serializers.DecimalField(max_digits=8, decimal_places=2)
    daily_pl = serializers.DecimalField(max_digits=12, decimal_places=2)
    daily_pl_percent = serializers.DecimalField(max_digits=8, decimal_places=2)
    company_name = serializers.CharField(max_length=200, required=False, allow_null=True)
    sector = serializers.CharField(max_length=100, required=False, allow_null=True)
    last_updated = serializers.DateTimeField()
    
    # Optional fields for options
    option_type = serializers.ChoiceField(
        choices=['call', 'put'], 
        required=False, 
        allow_null=True
    )
    strike_price = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        required=False, 
        allow_null=True
    )
    expiration_date = serializers.DateField(required=False, allow_null=True)
    contracts = serializers.IntegerField(required=False, allow_null=True)


class PortfolioSnapshotSerializer(serializers.Serializer):
    """Serializer for portfolio snapshots (historical data)."""
    
    timestamp = serializers.DateTimeField()
    total_value = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pl = serializers.DecimalField(max_digits=12, decimal_places=2)
    total_pl_percent = serializers.DecimalField(max_digits=8, decimal_places=2)
    daily_pl = serializers.DecimalField(max_digits=12, decimal_places=2)
    daily_pl_percent = serializers.DecimalField(max_digits=8, decimal_places=2)


class SyncPortfolioSerializer(serializers.Serializer):
    """Serializer for portfolio sync request."""
    
    force_full_sync = serializers.BooleanField(
        default=False,
        required=False,
        help_text="Force a full sync instead of incremental"
    )


class SyncResponseSerializer(serializers.Serializer):
    """Serializer for sync response."""
    
    status = serializers.CharField()
    message = serializers.CharField(required=False)
    synced_at = serializers.DateTimeField()
    portfolio = PortfolioSerializer(required=False)
    holdings_created = serializers.IntegerField(required=False)
    holdings_updated = serializers.IntegerField(required=False)
    total_holdings = serializers.IntegerField(required=False)


# NEW SERIALIZERS FOR ENHANCED DASHBOARD

class InvestmentOverviewSerializer(serializers.Serializer):
    """Serializer for investment overview metrics (margin & leverage)."""
    
    cash_invested = serializers.FloatField()
    margin_invested = serializers.FloatField()
    total_invested = serializers.FloatField()
    margin_available = serializers.FloatField()
    leverage_percent = serializers.FloatField()
    is_margin_account = serializers.BooleanField()
    message = serializers.CharField()


class PnLMetricsSerializer(serializers.Serializer):
    """Serializer for P&L metrics (YTD and today)."""
    
    ytd_pnl = serializers.FloatField()
    ytd_pnl_percent = serializers.FloatField()
    has_ytd_baseline = serializers.BooleanField()
    ytd_baseline_date = serializers.CharField(required=False, allow_null=True)
    today_pnl = serializers.FloatField()
    today_pnl_percent = serializers.FloatField()
    is_market_open = serializers.BooleanField()
    ytd_message = serializers.CharField()
    today_message = serializers.CharField()


class TopMoverSerializer(serializers.Serializer):
    """Serializer for individual top mover (winner or loser)."""
    
    symbol = serializers.CharField()
    company_name = serializers.CharField()
    asset_type = serializers.CharField()
    current_price = serializers.FloatField()
    previous_close = serializers.FloatField()
    price_change = serializers.FloatField()
    percent_change = serializers.FloatField()
    dollar_change = serializers.FloatField()
    market_value = serializers.FloatField()
    quantity = serializers.FloatField()


class TopHoldingSerializer(serializers.Serializer):
    """Serializer for top holding (concentration risk)."""
    
    symbol = serializers.CharField()
    company_name = serializers.CharField()
    market_value = serializers.FloatField()
    allocation_percent = serializers.FloatField()
    quantity = serializers.FloatField()
    asset_type = serializers.CharField()


class HoldingsAnalyticsSerializer(serializers.Serializer):
    """Serializer for complete holdings analytics."""
    
    total_holdings = serializers.IntegerField()
    stocks_count = serializers.IntegerField()
    options_count = serializers.IntegerField()
    crypto_count = serializers.IntegerField()
    top_holding = TopHoldingSerializer(required=False, allow_null=True)
    top_winner_percent = TopMoverSerializer(required=False, allow_null=True)
    top_loser_percent = TopMoverSerializer(required=False, allow_null=True)
    top_winner_dollar = TopMoverSerializer(required=False, allow_null=True)
    top_loser_dollar = TopMoverSerializer(required=False, allow_null=True)
    holdings_analyzed = serializers.IntegerField()


class HistoricalDataPointSerializer(serializers.Serializer):
    """Serializer for single historical data point (for charts)."""
    
    timestamp = serializers.DateTimeField()
    value = serializers.FloatField()
    change = serializers.FloatField(required=False, allow_null=True)
    change_percent = serializers.FloatField(required=False, allow_null=True)


class AllocationDataSerializer(serializers.Serializer):
    """Serializer for portfolio allocation data (pie chart)."""
    
    symbol = serializers.CharField()
    company_name = serializers.CharField()
    asset_type = serializers.CharField()
    market_value = serializers.FloatField()
    allocation_percent = serializers.FloatField()
    quantity = serializers.FloatField()
