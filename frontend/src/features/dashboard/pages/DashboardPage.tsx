/**
 * Dashboard Page
 * Main landing page showing enhanced portfolio dashboard
 */
import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Box, Divider, Typography, CircularProgress, Button, Paper } from '@mui/material';
import { AccountBalanceWallet as WalletIcon } from '@mui/icons-material';
import InvestmentOverview from '../components/investment/InvestmentOverview';
import PnLMetrics from '../components/pnl/PnLMetrics';
import HoldingsAnalytics from '../components/analytics/HoldingsAnalytics';
import PortfolioLineChart from '../components/charts/PortfolioLineChart';
import AllocationPieChart from '../components/charts/AllocationPieChart';
import { useAppDispatch, useAppSelector } from '../../../store';
import { fetchHistoricalData, fetchAllocationData } from '../../portfolio/store/portfolioSlice';
import { fetchAccounts } from '../../settings/store/robinhoodSlice';

export const DashboardPage = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const [selectedPeriod, setSelectedPeriod] = useState('1M');
  
  const { 
    historicalData, 
    allocationData, 
    isLoadingHistorical, 
    isLoadingAllocation
  } = useAppSelector((state) => state.portfolio);

  const { accounts, isLoading: isLoadingAccounts } = useAppSelector((state) => state.robinhood);

  // First, check if Robinhood accounts exist
  useEffect(() => {
    dispatch(fetchAccounts());
  }, [dispatch]);

  // Only fetch portfolio data if accounts exist
  useEffect(() => {
    if (accounts.length > 0) {
      dispatch(fetchHistoricalData(selectedPeriod));
      dispatch(fetchAllocationData());
    }
  }, [dispatch, selectedPeriod, accounts.length]);

  const handlePeriodChange = (period: string) => {
    setSelectedPeriod(period);
    if (accounts.length > 0) {
      dispatch(fetchHistoricalData(period));
    }
  };

  // Show loading while checking for accounts
  if (isLoadingAccounts) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  // Show empty state if no Robinhood accounts are linked
  if (accounts.length === 0) {
    return (
      <Box 
        sx={{ 
          display: 'flex', 
          justifyContent: 'center', 
          alignItems: 'center', 
          minHeight: '60vh',
          px: 2
        }}
      >
        <Paper
          elevation={2}
          sx={{
            p: 6,
            textAlign: 'center',
            maxWidth: 600,
            width: '100%'
          }}
        >
          <WalletIcon sx={{ fontSize: 80, color: 'primary.main', mb: 3 }} />
          <Typography variant="h4" gutterBottom fontWeight={600}>
            Connect Your Robinhood Account
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
            Link your Robinhood account in Settings to view your portfolio data, track your holdings, 
            and get insights into your investments.
          </Typography>
          <Button
            variant="contained"
            size="large"
            onClick={() => navigate('/settings')}
            sx={{ px: 4, py: 1.5 }}
          >
            Go to Settings
          </Button>
        </Paper>
      </Box>
    );
  }

  return (
    <Box sx={{ width: '100%' }}>
      {/* Investment Overview - Margin & Leverage Metrics */}
      <InvestmentOverview />
      
      <Divider sx={{ my: 2.5 }} />
      
      {/* P&L Metrics - YTD and Today */}
      <PnLMetrics />
      
      <Divider sx={{ my: 2.5 }} />
      
      {/* Holdings Analytics - Top Movers and Concentration */}
      <HoldingsAnalytics />
      
      <Divider sx={{ my: 2.5 }} />
      
      {/* Portfolio Allocation - Main Section (Full Width) */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
          Portfolio Allocation
        </Typography>
        {isLoadingAllocation ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <AllocationPieChart data={allocationData} />
        )}
      </Box>
      
      <Divider sx={{ my: 2.5 }} />
      
      {/* Portfolio Performance (Full Width) */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Portfolio Performance
        </Typography>
        {isLoadingHistorical ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <PortfolioLineChart
            data={historicalData}
            selectedPeriod={selectedPeriod}
            onPeriodChange={handlePeriodChange}
          />
        )}
      </Box>
    </Box>
  );
};

export default DashboardPage;
