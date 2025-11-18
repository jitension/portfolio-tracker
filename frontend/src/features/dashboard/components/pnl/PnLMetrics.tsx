/**
 * P&L Metrics Component
 * Displays Year-to-Date and Today's P&L performance
 */
import React, { useEffect } from 'react';
import { Box, Typography, CircularProgress, Grid } from '@mui/material';
import { useAppDispatch, useAppSelector } from '../../../../store';
import { fetchPnLMetrics } from '../../../portfolio/store/portfolioSlice';
import YTDPnLCard from './YTDPnLCard';
import TodayPnLCard from './TodayPnLCard';

const PnLMetrics: React.FC = () => {
  const dispatch = useAppDispatch();
  const { pnlMetrics, isLoadingPnL, error } = useAppSelector(
    (state) => state.portfolio
  );

  useEffect(() => {
    dispatch(fetchPnLMetrics());
  }, [dispatch]);

  if (isLoadingPnL) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error">Failed to load P&L metrics</Typography>
      </Box>
    );
  }

  if (!pnlMetrics) {
    return null;
  }

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Performance & P/L
      </Typography>
      <Grid container spacing={2} sx={{ width: '100%' }}>
        <Grid size={{ xs: 12, md: 6 }}>
          <YTDPnLCard
            ytdPnL={pnlMetrics.ytd_pnl}
            ytdPnLPercent={pnlMetrics.ytd_pnl_percent}
            hasBaseline={pnlMetrics.has_ytd_baseline}
            message={pnlMetrics.ytd_message}
          />
        </Grid>
        <Grid size={{ xs: 12, md: 6 }}>
          <TodayPnLCard
            todayPnL={pnlMetrics.today_pnl}
            todayPnLPercent={pnlMetrics.today_pnl_percent}
            isMarketOpen={pnlMetrics.is_market_open}
            message={pnlMetrics.today_message}
          />
        </Grid>
      </Grid>
    </Box>
  );
};

export default PnLMetrics;
