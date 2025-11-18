/**
 * Margin Invested Card
 * Displays margin borrowed/invested
 */
import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { TrendingUp } from '@mui/icons-material';

interface MarginInvestedCardProps {
  amount: number;
}

const MarginInvestedCard: React.FC<MarginInvestedCardProps> = ({ amount }) => {
  const hasMargin = amount > 0;

  return (
    <Card variant="outlined" sx={{ height: '100%', flexGrow: 1 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <TrendingUp sx={{ mr: 1, color: hasMargin ? 'warning.main' : 'text.secondary' }} />
          <Typography variant="body2" color="text.secondary">
            Margin Invested
          </Typography>
        </Box>
        <Typography 
          variant="h4" 
          component="div"
          color={hasMargin ? 'warning.main' : 'text.primary'}
        >
          ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {hasMargin ? 'Borrowed capital' : 'No margin used'}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default MarginInvestedCard;
