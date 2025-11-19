/**
 * Holdings Page Component
 * Main page displaying all portfolio holdings
 */
import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Container, Typography, Box, Paper, Card, CardContent, Stack, Button, CircularProgress } from '@mui/material';
import { AccountBalanceWallet as WalletIcon } from '@mui/icons-material';
import { useAppDispatch, useAppSelector } from '../../../store';
import { fetchAccounts } from '../../settings/store/robinhoodSlice';
import { HoldingsTable } from './HoldingsTable';

const formatCurrency = (value: number | string | null | undefined) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : (value || 0);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(numValue);
};

export const HoldingsPage = () => {
  const dispatch = useAppDispatch();
  const navigate = useNavigate();
  const { holdings } = useAppSelector((state) => state.holdings);
  const { accounts, isLoading: isLoadingAccounts } = useAppSelector((state) => state.robinhood);

  // Check for Robinhood accounts on mount
  useEffect(() => {
    dispatch(fetchAccounts());
  }, [dispatch]);

  // Show loading while checking for accounts
  if (isLoadingAccounts) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '60vh' }}>
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  // Show empty state if no Robinhood accounts are linked
  if (accounts.length === 0) {
    return (
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Box 
          sx={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            minHeight: '60vh'
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
              Link your Robinhood account in Settings to view your holdings and track your portfolio.
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
      </Container>
    );
  }

  // Calculate summary stats
  const totalValue = holdings.reduce((sum, holding) => {
    const value = typeof holding.market_value === 'string' 
      ? parseFloat(holding.market_value) 
      : holding.market_value;
    return sum + (value || 0);
  }, 0);

  const totalPL = holdings.reduce((sum, holding) => {
    const pl = typeof holding.total_pl === 'string' 
      ? parseFloat(holding.total_pl) 
      : holding.total_pl;
    return sum + (pl || 0);
  }, 0);

  const totalDailyPL = holdings.reduce((sum, holding) => {
    const pl = typeof holding.daily_pl === 'string' 
      ? parseFloat(holding.daily_pl) 
      : holding.daily_pl;
    return sum + (pl || 0);
  }, 0);

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      {/* Page Header */}
      <Box mb={4}>
        <Typography variant="h4" gutterBottom>
          Holdings
        </Typography>
        <Typography variant="body1" color="text.secondary">
          View and manage your portfolio holdings
        </Typography>
      </Box>

      {/* Summary Stats */}
      <Stack direction="row" spacing={3} sx={{ mb: 4, flexWrap: 'wrap' }}>
        <Card sx={{ minWidth: 250, flex: 1 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Total Holdings Value
            </Typography>
            <Typography variant="h5">
              {formatCurrency(totalValue)}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 250, flex: 1 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Total Holdings
            </Typography>
            <Typography variant="h5">
              {holdings.length}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 250, flex: 1 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Total P/L
            </Typography>
            <Typography 
              variant="h5" 
              color={totalPL >= 0 ? 'success.main' : 'error.main'}
            >
              {formatCurrency(totalPL)}
            </Typography>
          </CardContent>
        </Card>

        <Card sx={{ minWidth: 250, flex: 1 }}>
          <CardContent>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Today's P/L
            </Typography>
            <Typography 
              variant="h5" 
              color={totalDailyPL >= 0 ? 'success.main' : 'error.main'}
            >
              {formatCurrency(totalDailyPL)}
            </Typography>
          </CardContent>
        </Card>
      </Stack>

      {/* Holdings Table */}
      <Paper sx={{ p: 3 }}>
        <HoldingsTable />
      </Paper>
    </Container>
  );
};

export default HoldingsPage;
