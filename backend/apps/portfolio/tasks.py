"""
Celery tasks for Portfolio app.
Background jobs for data synchronization and maintenance.
"""
from celery import shared_task
from celery.utils.log import get_task_logger
from django.contrib.auth import get_user_model
from django.utils import timezone

from .services import PortfolioService, HoldingsService
from apps.robinhood.models import RobinhoodAccount
from core.exceptions import PortfolioSyncError

logger = get_task_logger(__name__)
User = get_user_model()


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def sync_portfolio_task(self, user_id, account_id=None):
    """
    Background task to sync portfolio data from Robinhood.
    
    Args:
        user_id: User ID
        account_id: Optional specific Robinhood account ID
        
    Returns:
        Dict with sync results
    """
    try:
        logger.info(f"Starting portfolio sync task for user {user_id}")
        
        # Get user
        user = User.objects.get(id=user_id)
        
        # Get Robinhood account
        if account_id:
            account = RobinhoodAccount.objects.get(id=account_id)
        else:
            accounts = RobinhoodAccount.get_user_accounts(user)
            if not accounts:
                raise ValueError(f"No Robinhood account found for user {user_id}")
            account = accounts.first()
        
        # Initialize services
        portfolio_service = PortfolioService(user, account)
        holdings_service = HoldingsService(user, account)
        
        # Sync portfolio summary
        portfolio_result = portfolio_service.sync_portfolio_data()
        
        # Sync holdings
        holdings_result = holdings_service.sync_holdings_data()
        
        logger.info(f"Portfolio sync completed for user {user_id}")
        
        return {
            'status': 'success',
            'user_id': user_id,
            'synced_at': timezone.now().isoformat(),
            'portfolio': portfolio_result,
            'holdings': holdings_result,
        }
    
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        raise
    
    except PortfolioSyncError as exc:
        logger.error(f"Portfolio sync failed for user {user_id}: {str(exc)}")
        # Retry the task
        raise self.retry(exc=exc)
    
    except Exception as exc:
        logger.error(
            f"Unexpected error in sync task for user {user_id}: {str(exc)}",
            exc_info=True
        )
        # Retry the task
        raise self.retry(exc=exc)


@shared_task
def create_daily_snapshots():
    """
    Create daily portfolio snapshots for all users.
    
    This task should be run once per day (e.g., at 11 PM).
    """
    logger.info("Starting daily snapshot creation")
    
    # Get all active Robinhood accounts
    accounts = RobinhoodAccount.objects.filter(is_active=True)
    
    snapshots_created = 0
    errors = 0
    
    for account in accounts:
        try:
            # Get user
            user = User.objects.get(id=account.user_id)
            
            # Create snapshot
            service = PortfolioService(user, account)
            snapshot = service.create_snapshot(snapshot_type='daily')
            
            snapshots_created += 1
            logger.info(
                f"Daily snapshot created for user {user.id}",
                extra={'user_id': user.id, 'snapshot_id': str(snapshot.id)}
            )
        
        except Exception as e:
            errors += 1
            logger.error(
                f"Failed to create daily snapshot for account {account.id}: {str(e)}",
                exc_info=True
            )
    
    logger.info(
        f"Daily snapshots completed: {snapshots_created} created, {errors} errors"
    )
    
    return {
        'snapshots_created': snapshots_created,
        'errors': errors,
        'completed_at': timezone.now().isoformat()
    }


@shared_task
def cleanup_old_snapshots():
    """
    Clean up old portfolio snapshots.
    
    Removes:
    - Manual snapshots older than 90 days
    - Keeps all daily snapshots (for historical tracking)
    """
    from .models import PortfolioSnapshot
    
    logger.info("Starting snapshot cleanup")
    
    # Delete manual snapshots older than 90 days
    cutoff_date = timezone.now() - timezone.timedelta(days=90)
    
    deleted_count = PortfolioSnapshot.objects(
        snapshot_type='manual',
        created_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted_count} old manual snapshots")
    
    return {
        'deleted_count': deleted_count,
        'completed_at': timezone.now().isoformat()
    }


@shared_task
def sync_all_portfolios():
    """
    Sync all active portfolios.
    
    This task can be run periodically to keep all portfolios up to date.
    Use with caution - may trigger many Robinhood API calls.
    """
    logger.info("Starting bulk portfolio sync")
    
    # Get all active accounts
    accounts = RobinhoodAccount.objects.filter(is_active=True)
    
    synced = 0
    failed = 0
    
    for account in accounts:
        try:
            # Queue individual sync task
            sync_portfolio_task.delay(account.user_id, str(account.id))
            synced += 1
        
        except Exception as e:
            failed += 1
            logger.error(
                f"Failed to queue sync for account {account.id}: {str(e)}",
                exc_info=True
            )
    
    logger.info(
        f"Bulk sync queued: {synced} accounts synced, {failed} failed"
    )
    
    return {
        'synced': synced,
        'failed': failed,
        'completed_at': timezone.now().isoformat()
    }
