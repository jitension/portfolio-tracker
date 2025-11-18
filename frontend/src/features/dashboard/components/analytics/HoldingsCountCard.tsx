/**
 * Holdings Count Card
 * Displays total holdings with breakdown
 */
import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { AccountTree } from '@mui/icons-material';

interface HoldingsCountCardProps {
  totalHoldings: number;
  stocksCount: number;
  optionsCount: number;
  cryptoCount: number;
}

const HoldingsCountCard: React.FC<HoldingsCountCardProps> = ({
  totalHoldings,
  stocksCount,
  optionsCount,
  cryptoCount,
}) => {
  return (
    <Card variant="outlined" sx={{ height: '100%', flexGrow: 1 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <AccountTree sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="body2" color="text.secondary">
            Total Holdings
          </Typography>
        </Box>
        <Typography variant="h4" component="div">
          {totalHoldings}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {stocksCount} stocks, {optionsCount} options, {cryptoCount} crypto
        </Typography>
      </CardContent>
    </Card>
  );
};

export default HoldingsCountCard;
