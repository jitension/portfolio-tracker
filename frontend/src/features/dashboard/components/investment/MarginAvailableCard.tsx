/**
 * Margin Available Card
 * Displays remaining margin credit available
 */
import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { CreditCard } from '@mui/icons-material';

interface MarginAvailableCardProps {
  amount: number;
}

const MarginAvailableCard: React.FC<MarginAvailableCardProps> = ({ amount }) => {
  return (
    <Card variant="outlined" sx={{ height: '100%', flexGrow: 1 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <CreditCard sx={{ mr: 1, color: 'info.main' }} />
          <Typography variant="body2" color="text.secondary">
            Margin Available
          </Typography>
        </Box>
        <Typography variant="h4" component="div">
          ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Additional buying power
        </Typography>
      </CardContent>
    </Card>
  );
};

export default MarginAvailableCard;
