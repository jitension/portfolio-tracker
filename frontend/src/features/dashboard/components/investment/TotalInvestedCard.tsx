/**
 * Total Invested Card
 * Displays total capital deployed (cash + margin)
 */
import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { Paid } from '@mui/icons-material';

interface TotalInvestedCardProps {
  amount: number;
}

const TotalInvestedCard: React.FC<TotalInvestedCardProps> = ({ amount }) => {
  return (
    <Card variant="outlined" sx={{ height: '100%', flexGrow: 1 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Paid sx={{ mr: 1, color: 'primary.main' }} />
          <Typography variant="body2" color="text.secondary">
            Total Invested
          </Typography>
        </Box>
        <Typography variant="h4" component="div">
          ${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Cash + margin deployed
        </Typography>
      </CardContent>
    </Card>
  );
};

export default TotalInvestedCard;
