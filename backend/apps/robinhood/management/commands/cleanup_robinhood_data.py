"""
Django management command to clean up Robinhood-related data.

This command cleans up:
- Inactive/deactivated RobinhoodAccounts
- Orphaned Portfolio records
- Orphaned Holdings
- Orphaned PortfolioSnapshots

Usage:
    # Preview what will be deleted (dry run)
    python manage.py cleanup_robinhood_data --dry-run
    
    # Actually perform the cleanup
    python manage.py cleanup_robinhood_data
    
    # Clean up for a specific user (non-superuser)
    python manage.py cleanup_robinhood_data --user-id 123
    
    # Clean up all non-superuser data
    python manage.py cleanup_robinhood_data --all-users
"""
from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from apps.robinhood.models import RobinhoodAccount
from apps.portfolio.models import Portfolio, Holding, PortfolioSnapshot

User = get_user_model()


class Command(BaseCommand):
    help = 'Clean up orphaned Robinhood and portfolio data for non-superuser accounts'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what will be deleted without actually deleting',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='Clean up data for a specific user ID (must not be superuser)',
        )
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Clean up data for all non-superuser accounts',
        )
        parser.add_argument(
            '--inactive-only',
            action='store_true',
            help='Only delete inactive/deactivated accounts and their data',
        )
    
    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options.get('user_id')
        all_users = options['all_users']
        inactive_only = options['inactive_only']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No data will actually be deleted\n'))
        
        # Summary counters
        summary = {
            'accounts': 0,
            'portfolios': 0,
            'holdings': 0,
            'snapshots': 0,
            'users_affected': set()
        }
        
        try:
            # Determine which accounts to clean
            if user_id:
                # Clean specific user
                user = User.objects.get(id=user_id)
                if user.is_superuser:
                    raise CommandError(f'Cannot clean up data for superuser account (ID: {user_id})')
                
                self.stdout.write(f'Cleaning up data for user: {user.username} (ID: {user_id})\n')
                self._cleanup_user_data(user_id, inactive_only, dry_run, summary)
            
            elif all_users:
                # Clean all non-superuser accounts
                self.stdout.write('Cleaning up data for all non-superuser accounts\n')
                non_superusers = User.objects.filter(is_superuser=False)
                
                for user in non_superusers:
                    self.stdout.write(f'\nProcessing user: {user.username} (ID: {user.id})')
                    self._cleanup_user_data(user.id, inactive_only, dry_run, summary)
            
            else:
                # Default: clean up inactive accounts only
                self.stdout.write('Cleaning up inactive/deactivated Robinhood accounts\n')
                inactive_accounts = RobinhoodAccount.objects(is_active=False)
                
                for account in inactive_accounts:
                    # Skip superuser accounts
                    try:
                        user = User.objects.get(id=account.user_id)
                        if user.is_superuser:
                            self.stdout.write(
                                self.style.WARNING(f'  Skipping superuser account: {account.account_number}')
                            )
                            continue
                    except User.DoesNotExist:
                        self.stdout.write(
                            self.style.WARNING(f'  User {account.user_id} not found for account {account.account_number}')
                        )
                    
                    self.stdout.write(f'\n  Cleaning account: {account.account_number} (User ID: {account.user_id})')
                    
                    if not dry_run:
                        deleted = account.delete_with_related_data()
                        summary['accounts'] += deleted.get('account', 0)
                        summary['portfolios'] += deleted.get('portfolio', 0)
                        summary['holdings'] += deleted.get('holdings', 0)
                        summary['snapshots'] += deleted.get('snapshots', 0)
                        summary['users_affected'].add(account.user_id)
                    else:
                        # Preview mode
                        holdings_count = Holding.objects(robinhood_account_id=account.id).count()
                        snapshots_count = PortfolioSnapshot.objects(robinhood_account_id=account.id).count()
                        portfolio_exists = Portfolio.objects(robinhood_account_id=account.id).first() is not None
                        
                        self.stdout.write(f'    - Holdings: {holdings_count}')
                        self.stdout.write(f'    - Snapshots: {snapshots_count}')
                        self.stdout.write(f'    - Portfolio: {"Yes" if portfolio_exists else "No"}')
                        
                        summary['accounts'] += 1
                        summary['portfolios'] += 1 if portfolio_exists else 0
                        summary['holdings'] += holdings_count
                        summary['snapshots'] += snapshots_count
                        summary['users_affected'].add(account.user_id)
            
            # Print summary
            self.stdout.write('\n' + '='*60)
            if dry_run:
                self.stdout.write(self.style.WARNING('\nDRY RUN SUMMARY (No data was deleted):'))
            else:
                self.stdout.write(self.style.SUCCESS('\nCLEANUP SUMMARY:'))
            
            self.stdout.write(f'  Users affected: {len(summary["users_affected"])}')
            self.stdout.write(f'  Accounts deleted: {summary["accounts"]}')
            self.stdout.write(f'  Portfolios deleted: {summary["portfolios"]}')
            self.stdout.write(f'  Holdings deleted: {summary["holdings"]}')
            self.stdout.write(f'  Snapshots deleted: {summary["snapshots"]}')
            self.stdout.write('='*60 + '\n')
            
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('Run without --dry-run to actually delete the data')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS('Cleanup completed successfully!')
                )
        
        except User.DoesNotExist:
            raise CommandError(f'User with ID {user_id} does not exist')
        except Exception as e:
            raise CommandError(f'Error during cleanup: {str(e)}')
    
    def _cleanup_user_data(self, user_id, inactive_only, dry_run, summary):
        """Clean up all Robinhood data for a specific user."""
        # Get user's accounts
        if inactive_only:
            accounts = RobinhoodAccount.objects(user_id=user_id, is_active=False)
        else:
            accounts = RobinhoodAccount.objects(user_id=user_id)
        
        if not accounts:
            self.stdout.write(self.style.WARNING('  No accounts found'))
            return
        
        for account in accounts:
            status = 'inactive' if not account.is_active else 'active'
            self.stdout.write(f'  Processing {status} account: {account.account_number}')
            
            if not dry_run:
                deleted = account.delete_with_related_data()
                summary['accounts'] += deleted.get('account', 0)
                summary['portfolios'] += deleted.get('portfolio', 0)
                summary['holdings'] += deleted.get('holdings', 0)
                summary['snapshots'] += deleted.get('snapshots', 0)
                summary['users_affected'].add(user_id)
                
                self.stdout.write(self.style.SUCCESS(
                    f'    Deleted: {deleted["holdings"]} holdings, '
                    f'{deleted["snapshots"]} snapshots, '
                    f'{deleted["portfolio"]} portfolio'
                ))
            else:
                # Preview mode
                holdings_count = Holding.objects(robinhood_account_id=account.id).count()
                snapshots_count = PortfolioSnapshot.objects(robinhood_account_id=account.id).count()
                portfolio_exists = Portfolio.objects(robinhood_account_id=account.id).first() is not None
                
                self.stdout.write(f'    Would delete:')
                self.stdout.write(f'      - Holdings: {holdings_count}')
                self.stdout.write(f'      - Snapshots: {snapshots_count}')
                self.stdout.write(f'      - Portfolio: {"Yes" if portfolio_exists else "No"}')
                
                summary['accounts'] += 1
                summary['portfolios'] += 1 if portfolio_exists else 0
                summary['holdings'] += holdings_count
                summary['snapshots'] += snapshots_count
                summary['users_affected'].add(user_id)
