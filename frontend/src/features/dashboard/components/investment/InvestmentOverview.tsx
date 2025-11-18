/**
 * Investment Overview Component
 * Displays investment metrics including margin and leverage
 */
import React, { useEffect } from 'react';
import { Box, Typography, CircularProgress, Button, Grid } from '@mui/material';
import { Sync as SyncIcon } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../../../store';
import { 
  fetchInvestmentMetrics,
  fetchPnLMetrics,
  fetchHoldingsAnalytics,
  fetchHistoricalData,
  fetchAllocationData,
  syncPortfolio 
} from '../../../portfolio/store/portfolioSlice';
import CashInvestedCard from './CashInvestedCard';
import MarginInvestedCard from './MarginInvestedCard';
import TotalInvestedCard from './TotalInvestedCard';
import MarginAvailableCard from './MarginAvailableCard';
import LeverageCard from './LeverageCard';

const InvestmentOverview: React.FC = () => {
  const dispatch = useAppDispatch();
  const { investmentMetrics, isLoadingInvestment, isLoading, error } = useAppSelector(
    (state) => state.portfolio
  );

  useEffect(() => {
    dispatch(fetchInvestmentMetrics());
  }, [dispatch]);

  const handleSync = async () => {
    // Sync portfolio data from Robinhood
    await dispatch(syncPortfolio());
    
    // Refresh all dashboard data
    dispatch(fetchInvestmentMetrics());
    dispatch(fetchPnLMetrics());
    dispatch(fetchHoldingsAnalytics());
    dispatch(fetchHistoricalData('1M'));
    dispatch(fetchAllocationData());
  };

  const isSyncing = isLoading;

  if (isLoadingInvestment) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error">Failed to load investment metrics</Typography>
      </Box>
    );
  }

  if (!investmentMetrics) {
    return null;
  }

  return (
    <Box sx={{ mb: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
        <Typography variant="h6">
          Investment Overview
        </Typography>
        <Button
          variant="contained"
          startIcon={isSyncing ? <CircularProgress size={20} color="inherit" /> : <SyncIcon />}
          onClick={handleSync}
          disabled={isSyncing}
        >
          {isSyncing ? 'Syncing...' : 'Sync'}
        </Button>
      </Box>
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, md: 6, lg: 4 }}>
          <CashInvestedCard amount={investmentMetrics.cash_invested} />
        </Grid>
        <Grid size={{ xs: 12, md: 6, lg: 4 }}>
          <MarginInvestedCard amount={investmentMetrics.margin_invested} />
        </Grid>
        <Grid size={{ xs: 12, md: 6, lg: 4 }}>
          <TotalInvestedCard amount={investmentMetrics.total_invested} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <MarginAvailableCard amount={investmentMetrics.margin_available} />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <LeverageCard
            leveragePercent={investmentMetrics.leverage_percent}
            isMarginAccount={investmentMetrics.is_margin_account}
            message={investmentMetrics.message}
          />
        </Grid>
      </Grid>
    </Box>
  );
};

export default InvestmentOverview;
