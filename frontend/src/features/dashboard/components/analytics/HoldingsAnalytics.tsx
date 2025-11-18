/**
 * Holdings Analytics Component
 * Displays holdings statistics and top movers
 */
import React, { useEffect } from 'react';
import { Box, Typography, CircularProgress, Grid } from '@mui/material';
import { useAppDispatch, useAppSelector } from '../../../../store';
import { fetchHoldingsAnalytics } from '../../../portfolio/store/portfolioSlice';
import HoldingsCountCard from './HoldingsCountCard';
import TopHoldingCard from './TopHoldingCard';
import TopMoverCard from './TopMoverCard';

const HoldingsAnalytics: React.FC = () => {
  const dispatch = useAppDispatch();
  const { holdingsAnalytics, isLoadingAnalytics, error } = useAppSelector(
    (state) => state.portfolio
  );

  useEffect(() => {
    dispatch(fetchHoldingsAnalytics());
  }, [dispatch]);

  if (isLoadingAnalytics) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 2 }}>
        <Typography color="error">Failed to load holdings analytics</Typography>
      </Box>
    );
  }

  if (!holdingsAnalytics) {
    return null;
  }

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h6" sx={{ mb: 2 }}>
        Holdings Analytics
      </Typography>
      
      {/* Holdings Count and Top Holding */}
      <Grid container spacing={2} sx={{ width: '100%', mb: 2 }}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <HoldingsCountCard
            totalHoldings={holdingsAnalytics.total_holdings}
            stocksCount={holdingsAnalytics.stocks_count}
            optionsCount={holdingsAnalytics.options_count}
            cryptoCount={holdingsAnalytics.crypto_count}
          />
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          {holdingsAnalytics.top_holding && (
            <TopHoldingCard holding={holdingsAnalytics.top_holding} />
          )}
        </Grid>
      </Grid>

      {/* Top Movers Grid */}
      <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1, mt: 2 }}>
        Top Movers (Today)
      </Typography>
      <Grid container spacing={3} sx={{ width: '100%' }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          {holdingsAnalytics.top_winner_percent && (
            <TopMoverCard
              title="Top Winner %"
              mover={holdingsAnalytics.top_winner_percent}
              isWinner={true}
              sortBy="percent"
            />
          )}
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          {holdingsAnalytics.top_loser_percent && (
            <TopMoverCard
              title="Top Loser %"
              mover={holdingsAnalytics.top_loser_percent}
              isWinner={false}
              sortBy="percent"
            />
          )}
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          {holdingsAnalytics.top_winner_dollar && (
            <TopMoverCard
              title="Top Winner $"
              mover={holdingsAnalytics.top_winner_dollar}
              isWinner={true}
              sortBy="dollar"
            />
          )}
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          {holdingsAnalytics.top_loser_dollar && (
            <TopMoverCard
              title="Top Loser $"
              mover={holdingsAnalytics.top_loser_dollar}
              isWinner={false}
              sortBy="dollar"
            />
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default HoldingsAnalytics;
