"""
Portfolio models using MongoEngine.
Stores portfolio summaries, holdings, and historical snapshots.
"""
from mongoengine import Document, EmbeddedDocument, fields
from django.utils import timezone
import logging

logger = logging.getLogger('apps')


class Portfolio(Document):
    """
    MongoEngine Document for storing portfolio summary data.
    
    Represents the current state of a user's portfolio including
    total value, P&L, and breakdown by asset type.
    """
    
    # References
    user_id = fields.IntField(required=True)
    robinhood_account_id = fields.ObjectIdField(required=True)
    
    # Portfolio Values
    total_value = fields.DecimalField(precision=2, default=0.0)
    total_equity = fields.DecimalField(precision=2, default=0.0)
    cash = fields.DecimalField(precision=2, default=0.0)
    buying_power = fields.DecimalField(precision=2, default=0.0)
    
    # Profit & Loss Metrics
    total_pl = fields.DecimalField(precision=2, default=0.0)
    total_pl_percent = fields.DecimalField(precision=2, default=0.0)
    daily_pl = fields.DecimalField(precision=2, default=0.0)
    daily_pl_percent = fields.DecimalField(precision=2, default=0.0)
    
    # Asset Breakdown
    stocks_value = fields.DecimalField(precision=2, default=0.0)
    options_value = fields.DecimalField(precision=2, default=0.0)
    crypto_value = fields.DecimalField(precision=2, default=0.0)
    
    # Holdings Counts
    holdings_count = fields.IntField(default=0)
    stocks_count = fields.IntField(default=0)
    options_count = fields.IntField(default=0)
    crypto_count = fields.IntField(default=0)
    
    # Margin & Leverage Metrics (NEW - Enhanced Dashboard)
    margin_invested = fields.DecimalField(precision=2, default=0.0)
    margin_available = fields.DecimalField(precision=2, default=0.0)
    leverage_percent = fields.DecimalField(precision=2, default=100.0)  # 100% = no leverage
    cash_invested = fields.DecimalField(precision=2, default=0.0)  # Cash without margin
    
    # Market Status
    market_status = fields.StringField(
        choices=['open', 'closed', 'extended'],
        default='closed'
    )
    
    # Timestamps
    last_updated = fields.DateTimeField(default=timezone.now)
    created_at = fields.DateTimeField(default=timezone.now)
    
    # Database configuration
    meta = {
        'collection': 'portfolios',
        'indexes': [
            'user_id',
            'robinhood_account_id',
            {'fields': ['user_id', 'robinhood_account_id'], 'unique': True},
            '-last_updated',
        ],
        'ordering': ['-last_updated']
    }
    
    def __str__(self):
        return f"Portfolio(User: {self.user_id}, Value: ${self.total_value})"
    
    def update_values(self, portfolio_data):
        """Update portfolio values from dictionary."""
        for key, value in portfolio_data.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.last_updated = timezone.now()
        self.save()
        
        logger.info(
            f"Portfolio updated for user {self.user_id}: ${self.total_value}",
            extra={'user_id': self.user_id, 'portfolio_id': str(self.id)}
        )
    
    @classmethod
    def get_or_create_for_user(cls, user_id, account_id):
        """Get existing portfolio or create new one."""
        portfolio = cls.objects(
            user_id=user_id,
            robinhood_account_id=account_id
        ).first()
        
        if not portfolio:
            portfolio = cls(
                user_id=user_id,
                robinhood_account_id=account_id
            )
            portfolio.save()
            logger.info(
                f"Created new portfolio for user {user_id}",
                extra={'user_id': user_id}
            )
        
        return portfolio


class Holding(Document):
    """
    MongoEngine Document for storing individual holdings (stocks, options, crypto).
    
    Represents a position in a specific security including quantity,
    cost basis, current value, and P&L calculations.
    """
    
    # References
    user_id = fields.IntField(required=True)
    robinhood_account_id = fields.ObjectIdField(required=True)
    portfolio_id = fields.ObjectIdField()
    
    # Security Information
    symbol = fields.StringField(required=True, max_length=20)
    asset_type = fields.StringField(
        required=True,
        choices=['stock', 'option', 'crypto']
    )
    
    # Position Details
    quantity = fields.DecimalField(precision=8, required=True)
    average_cost = fields.DecimalField(precision=2, required=True)
    current_price = fields.DecimalField(precision=2, required=True)
    market_value = fields.DecimalField(precision=2, required=True)
    
    # Profit & Loss
    total_pl = fields.DecimalField(precision=2, default=0.0)
    total_pl_percent = fields.DecimalField(precision=2, default=0.0)
    daily_pl = fields.DecimalField(precision=2, default=0.0)
    daily_pl_percent = fields.DecimalField(precision=2, default=0.0)
    
    # Stock-Specific Fields
    company_name = fields.StringField(max_length=200)
    sector = fields.StringField(max_length=100)
    pe_ratio = fields.DecimalField(precision=2)
    dividend_yield = fields.DecimalField(precision=4)
    
    # Option-Specific Fields (null for stocks/crypto)
    option_type = fields.StringField(choices=['call', 'put'])
    strike_price = fields.DecimalField(precision=2)
    expiration_date = fields.DateField()
    contracts = fields.IntField()
    
    # Greeks (for options)
    delta = fields.DecimalField(precision=4)
    gamma = fields.DecimalField(precision=4)
    theta = fields.DecimalField(precision=4)
    vega = fields.DecimalField(precision=4)
    rho = fields.DecimalField(precision=4)
    
    # Status
    is_active = fields.BooleanField(default=True)
    
    # Timestamps
    last_updated = fields.DateTimeField(default=timezone.now)
    created_at = fields.DateTimeField(default=timezone.now)
    closed_at = fields.DateTimeField()
    
    # Database configuration
    meta = {
        'collection': 'holdings',
        'indexes': [
            'user_id',
            'robinhood_account_id',
            'symbol',
            {'fields': ['user_id', 'symbol', 'is_active']},
            {'fields': ['user_id', 'asset_type', 'is_active']},
            {'fields': ['user_id', 'is_active']},
            '-last_updated',
            {'fields': ['expiration_date'], 'sparse': True},
        ],
        'ordering': ['-market_value']
    }
    
    def __str__(self):
        return f"Holding({self.symbol}, {self.asset_type}, {self.quantity} @ ${self.current_price})"
    
    def calculate_pl(self):
        """Calculate profit/loss metrics."""
        cost_basis = float(self.average_cost) * float(self.quantity)
        current_value = float(self.market_value)
        
        if cost_basis > 0:
            self.total_pl = current_value - cost_basis
            self.total_pl_percent = (self.total_pl / cost_basis) * 100
        else:
            self.total_pl = 0
            self.total_pl_percent = 0
        
        # Daily P&L calculation would require previous day's price
        # For now, set to 0 - will be enhanced later
        self.daily_pl = 0
        self.daily_pl_percent = 0
    
    def update_from_data(self, holding_data):
        """Update holding from dictionary data."""
        for key, value in holding_data.items():
            if hasattr(self, key) and value is not None:
                setattr(self, key, value)
        
        # Recalculate P&L
        self.calculate_pl()
        self.last_updated = timezone.now()
        self.save()
        
        logger.debug(
            f"Holding updated: {self.symbol} - ${self.market_value}",
            extra={'user_id': self.user_id, 'symbol': self.symbol}
        )
    
    def close_position(self):
        """Mark position as closed."""
        self.is_active = False
        self.closed_at = timezone.now()
        self.save()
        
        logger.info(
            f"Position closed: {self.symbol}",
            extra={'user_id': self.user_id, 'symbol': self.symbol}
        )
    
    @classmethod
    def get_user_holdings(cls, user_id, active_only=True):
        """Get all holdings for a user."""
        query = {'user_id': user_id}
        if active_only:
            query['is_active'] = True
        return cls.objects(**query)
    
    @classmethod
    def get_holding_by_symbol(cls, user_id, symbol, asset_type='stock'):
        """Get a specific holding by symbol."""
        return cls.objects(
            user_id=user_id,
            symbol=symbol,
            asset_type=asset_type,
            is_active=True
        ).first()


class PortfolioSnapshot(Document):
    """
    MongoEngine Document for storing historical portfolio snapshots.
    
    Used to track portfolio performance over time and generate
    historical charts and analytics.
    """
    
    # References
    user_id = fields.IntField(required=True)
    robinhood_account_id = fields.ObjectIdField(required=True)
    
    # Snapshot Metadata
    timestamp = fields.DateTimeField(required=True, default=timezone.now)
    snapshot_type = fields.StringField(
        required=True,
        choices=['daily', 'manual', 'sync'],
        default='manual'
    )
    
    # Portfolio Values (copied from Portfolio at time of snapshot)
    total_value = fields.DecimalField(precision=2, required=True)
    total_equity = fields.DecimalField(precision=2, required=True)
    cash = fields.DecimalField(precision=2, required=True)
    buying_power = fields.DecimalField(precision=2, required=True)
    
    # P&L Metrics
    daily_pl = fields.DecimalField(precision=2, default=0.0)
    daily_pl_percent = fields.DecimalField(precision=2, default=0.0)
    total_pl = fields.DecimalField(precision=2, default=0.0)
    total_pl_percent = fields.DecimalField(precision=2, default=0.0)
    
    # Asset Breakdown
    stocks_value = fields.DecimalField(precision=2, default=0.0)
    options_value = fields.DecimalField(precision=2, default=0.0)
    crypto_value = fields.DecimalField(precision=2, default=0.0)
    
    # Holdings Counts
    holdings_count = fields.IntField(default=0)
    stocks_count = fields.IntField(default=0)
    options_count = fields.IntField(default=0)
    crypto_count = fields.IntField(default=0)
    
    # Market Benchmarks (for comparison)
    sp500_value = fields.DecimalField(precision=2)
    nasdaq_value = fields.DecimalField(precision=2)
    market_status = fields.StringField(
        choices=['open', 'closed', 'extended'],
        default='closed'
    )
    
    # Timestamp
    created_at = fields.DateTimeField(default=timezone.now)
    
    # Database configuration
    meta = {
        'collection': 'portfolio_snapshots',
        'indexes': [
            'user_id',
            'robinhood_account_id',
            {'fields': ['user_id', '-timestamp']},
            {'fields': ['robinhood_account_id', '-timestamp']},
            {'fields': ['snapshot_type', '-timestamp']},
            '-timestamp',
        ],
        'ordering': ['-timestamp']
    }
    
    def __str__(self):
        return f"Snapshot({self.timestamp}, ${self.total_value})"
    
    @classmethod
    def create_from_portfolio(cls, portfolio, snapshot_type='manual'):
        """Create a snapshot from current portfolio state."""
        snapshot = cls(
            user_id=portfolio.user_id,
            robinhood_account_id=portfolio.robinhood_account_id,
            snapshot_type=snapshot_type,
            total_value=portfolio.total_value,
            total_equity=portfolio.total_equity,
            cash=portfolio.cash,
            buying_power=portfolio.buying_power,
            daily_pl=portfolio.daily_pl,
            daily_pl_percent=portfolio.daily_pl_percent,
            total_pl=portfolio.total_pl,
            total_pl_percent=portfolio.total_pl_percent,
            stocks_value=portfolio.stocks_value,
            options_value=portfolio.options_value,
            crypto_value=portfolio.crypto_value,
            holdings_count=portfolio.holdings_count,
            stocks_count=portfolio.stocks_count,
            options_count=portfolio.options_count,
            crypto_count=portfolio.crypto_count,
            market_status=portfolio.market_status,
        )
        snapshot.save()
        
        logger.info(
            f"Portfolio snapshot created: {snapshot_type}",
            extra={'user_id': portfolio.user_id, 'snapshot_id': str(snapshot.id)}
        )
        
        return snapshot
    
    @classmethod
    def get_user_snapshots(cls, user_id, snapshot_type=None, days=None):
        """Get snapshots for a user with optional filters."""
        query = {'user_id': user_id}
        
        if snapshot_type:
            query['snapshot_type'] = snapshot_type
        
        if days:
            start_date = timezone.now() - timezone.timedelta(days=days)
            query['timestamp__gte'] = start_date
        
        return cls.objects(**query)
    
    @classmethod
    def get_latest_snapshot(cls, user_id):
        """Get the most recent snapshot for a user."""
        return cls.objects(user_id=user_id).first()
