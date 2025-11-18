/**
 * Holdings Page Component
 * Main page displaying all portfolio holdings
 */
import { Container, Typography, Box, Paper, Card, CardContent, Stack } from '@mui/material';
import { useAppSelector } from '../../../store';
import { HoldingsTable } from './HoldingsTable';

const formatCurrency = (value: number | string | null | undefined) => {
  const numValue = typeof value === 'string' ? parseFloat(value) : (value || 0);
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
  }).format(numValue);
};

export const HoldingsPage = () => {
  const { holdings } = useAppSelector((state) => state.holdings);

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
