/**
 * Portfolio Summary Component
 * Displays portfolio metrics and summary
 */
import { useEffect } from 'react';
import { Container, Card, CardContent, Typography, Button, CircularProgress, Box, Stack } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useAppDispatch, useAppSelector } from '../../../store';
import { fetchPortfolioSummary, syncPortfolio } from '../store/portfolioSlice';

const formatCurrency = (value: number | string | null | undefined) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : (value || 0);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(numValue);
};

const formatPercent = (value: number | string | null | undefined) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : (value || 0);
  return `${numValue >= 0 ? '+' : ''}${numValue.toFixed(2)}%`;
};

export const PortfolioSummary = () => {
  const dispatch = useAppDispatch();
  const { summary, isLoading, lastSynced } = useAppSelector((state) => state.portfolio);

  useEffect(() => {
    dispatch(fetchPortfolioSummary());
  }, [dispatch]);

  const handleSync = () => {
    dispatch(syncPortfolio());
  };

  if (isLoading && !summary) {
    return (
      <Container>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (!summary) {
    return (
      <Container>
        <Typography variant="h6" color="error">
          Failed to load portfolio data
        </Typography>
      </Container>
    );
  }

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Header with Sync Button */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4">Portfolio Summary</Typography>
        <Button
          variant="contained"
          startIcon={<RefreshIcon />}
          onClick={handleSync}
          disabled={isLoading}
        >
          Sync
        </Button>
      </Box>

      {/* Summary Cards */}
      <Stack direction="row" spacing={3} sx={{ flexWrap: 'wrap', gap: 2 }}>
        {/* Total Value */}
        <Card sx={{ minWidth: 250, flex: 1 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Total Value
            </Typography>
            <Typography variant="h4">
              {formatCurrency(summary.total_value)}
            </Typography>
          </CardContent>
        </Card>

        {/* Total P/L */}
        <Card sx={{ minWidth: 250, flex: 1 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Total P/L
            </Typography>
            <Typography 
              variant="h4" 
              color={summary.total_pl >= 0 ? 'success.main' : 'error.main'}
            >
              {formatCurrency(summary.total_pl)}
            </Typography>
            <Typography 
              variant="body2" 
              color={summary.total_pl_percent >= 0 ? 'success.main' : 'error.main'}
            >
              {formatPercent(summary.total_pl_percent)}
            </Typography>
          </CardContent>
        </Card>

        {/* Today's Change */}
        <Card sx={{ minWidth: 250, flex: 1 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Today's Change
            </Typography>
            <Typography 
              variant="h4" 
              color={summary.daily_pl >= 0 ? 'success.main' : 'error.main'}
            >
              {formatCurrency(summary.daily_pl)}
            </Typography>
            <Typography 
              variant="body2" 
              color={summary.daily_pl_percent >= 0 ? 'success.main' : 'error.main'}
            >
              {formatPercent(summary.daily_pl_percent)}
            </Typography>
          </CardContent>
        </Card>

        {/* Holdings Count */}
        <Card sx={{ minWidth: 250, flex: 1 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Holdings
            </Typography>
            <Typography variant="h4">
              {summary.holdings_count}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {summary.stocks_count} stocks
            </Typography>
          </CardContent>
        </Card>
      </Stack>

      {/* Last Synced */}
      {lastSynced && (
        <Box mt={2}>
          <Typography variant="caption" color="text.secondary">
            Last synced: {new Date(lastSynced).toLocaleString()}
          </Typography>
        </Box>
      )}
    </Container>
  );
};

export default PortfolioSummary;
