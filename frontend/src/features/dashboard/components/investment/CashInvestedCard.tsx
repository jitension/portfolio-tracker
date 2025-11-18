/**
 * Cash Invested Card
 * Displays cash invested (without margin)
 */
import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { AccountBalance } from '@mui/icons-material';

interface CashInvestedCardProps {
  amount: number;
}

const CashInvestedCard: React.FC<CashInvestedCardProps> = ({ amount }) => {
  return (
    <Card variant="outlined" sx={{ height: '100%', flexGrow: 1 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <AccountBalance sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="body2" color="text.secondary">
            Cash Invested
          </Typography>
        </Box>
        <Typography variant="h4" component="div">
          ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Your capital without margin
        </Typography>
      </CardContent>
    </Card>
  );
};

export default CashInvestedCard;
