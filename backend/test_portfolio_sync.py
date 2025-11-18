"""
Test script for portfolio synchronization.
Run this to test the portfolio sync with your real Robinhood account.

Usage:
    python test_portfolio_sync.py
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from apps.robinhood.models import RobinhoodAccount
from apps.portfolio.services import PortfolioService, HoldingsService
from apps.portfolio.models import Portfolio, Holding

User = get_user_model()


def test_portfolio_sync():
    """Test portfolio synchronization."""
    print("=" * 80)
    print("PORTFOLIO SYNC TEST")
    print("=" * 80)
    
    # Get test user
    print("\n1. Getting user...")
    user = User.objects.filter(email='your-email@example.com').first()
    if not user:
        print("❌ User not found. Please create a user first.")
        print("   Update this script with your actual email address.")
        return False
    print(f"✅ User found: {user.email} (ID: {user.id})")
    
    # Get Robinhood account
    print("\n2. Getting Robinhood account...")
    rh_account = RobinhoodAccount.get_user_accounts(user).first()
    if not rh_account:
        print("❌ No Robinhood account found for user.")
        return False
    print(f"✅ Robinhood account found: {rh_account.account_number}")
    
    # Test portfolio service
    print("\n3. Testing PortfolioService...")
    try:
        portfolio_service = PortfolioService(user, rh_account)
        print("✅ PortfolioService initialized")
    except Exception as e:
        print(f"❌ Failed to initialize PortfolioService: {e}")
        return False
    
    # Sync portfolio data
    print("\n4. Syncing portfolio data from Robinhood...")
    print("   This will:")
    print("   - Authenticate with Robinhood")
    print("   - Fetch portfolio summary")
    print("   - Update MongoDB")
    print("   - Create snapshot")
    try:
        result = portfolio_service.sync_portfolio_data()
        print(f"✅ Portfolio sync completed!")
        print(f"   Status: {result['status']}")
        print(f"   Synced at: {result['synced_at']}")
    except Exception as e:
        print(f"❌ Portfolio sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test holdings service
    print("\n5. Syncing holdings data...")
    try:
        holdings_service = HoldingsService(user, rh_account)
        holdings_result = holdings_service.sync_holdings_data()
        print(f"✅ Holdings sync completed!")
        print(f"   Created: {holdings_result['holdings_created']}")
        print(f"   Updated: {holdings_result['holdings_updated']}")
        print(f"   Total: {holdings_result['total_holdings']}")
    except Exception as e:
        print(f"❌ Holdings sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Display portfolio summary
    print("\n6. Getting portfolio summary...")
    try:
        summary = portfolio_service.get_portfolio_summary(use_cache=False)
        print(f"✅ Portfolio Summary:")
        print(f"   Total Value: ${summary['total_value']:,.2f}")
        print(f"   Total P/L: ${summary['total_pl']:,.2f} ({summary['total_pl_percent']:.2f}%)")
        print(f"   Daily P/L: ${summary['daily_pl']:,.2f} ({summary['daily_pl_percent']:.2f}%)")
        print(f"   Cash: ${summary['cash']:,.2f}")
        print(f"   Stocks: ${summary['stocks_value']:,.2f}")
        print(f"   Holdings Count: {summary['holdings_count']}")
    except Exception as e:
        print(f"❌ Failed to get summary: {e}")
        return False
    
    # Display holdings
    print("\n7. Getting holdings...")
    try:
        holdings = holdings_service.get_holdings(use_cache=False)
        print(f"✅ Holdings ({len(holdings)} total):")
        for holding in holdings[:10]:  # Show first 10
            print(f"   {holding['symbol']:6} | "
                  f"Qty: {holding['quantity']:>10} | "
                  f"Price: ${holding['current_price']:>8.2f} | "
                  f"Value: ${holding['market_value']:>10.2f} | "
                  f"P/L: {holding['total_pl_percent']:>6.2f}%")
        if len(holdings) > 10:
            print(f"   ... and {len(holdings) - 10} more")
    except Exception as e:
        print(f"❌ Failed to get holdings: {e}")
        return False
    
    # Verify MongoDB data
    print("\n8. Verifying MongoDB data...")
    portfolio_count = Portfolio.objects(user_id=user.id).count()
    holdings_count = Holding.objects(user_id=user.id, is_active=True).count()
    print(f"✅ MongoDB verification:")
    print(f"   Portfolios in DB: {portfolio_count}")
    print(f"   Holdings in DB: {holdings_count}")
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS PASSED!")
    print("=" * 80)
    return True


if __name__ == '__main__':
    success = test_portfolio_sync()
    sys.exit(0 if success else 1)
