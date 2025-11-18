/**
 * Top Holding Card
 * Displays largest holding (concentration risk)
 */
import React from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { Star } from '@mui/icons-material';
import type { TopHolding } from '../../../../types/portfolio';

interface TopHoldingCardProps {
  holding: TopHolding;
}

const TopHoldingCard: React.FC<TopHoldingCardProps> = ({ holding }) => {
  // Determine concentration risk level and color
  const getRiskLevel = (percent: number) => {
    if (percent < 10) return { label: 'Well Diversified', color: 'success' as const };
    if (percent < 20) return { label: 'Moderate', color: 'warning' as const };
    if (percent < 30) return { label: 'High Concentration', color: 'error' as const };
    return { label: 'Very High', color: 'error' as const };
  };

  const risk = getRiskLevel(holding.allocation_percent);

  return (
    <Card variant="outlined" sx={{ height: '100%', flexGrow: 1 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Star sx={{ mr: 1, color: 'primary.main' }} />
            <Typography variant="body2" color="text.secondary">
              Top Holding
            </Typography>
          </Box>
          <Chip label={risk.label} size="small" color={risk.color} />
        </Box>
        <Typography variant="h5" component="div" sx={{ fontWeight: 600 }}>
          {holding.symbol}
        </Typography>
        <Typography variant="body2" color="text.secondary" noWrap>
          {holding.company_name}
        </Typography>
        <Typography variant="h6" sx={{ mt: 1 }} color={`${risk.color}.main`}>
          {holding.allocation_percent.toFixed(1)}% of portfolio
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
          ${holding.market_value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default TopHoldingCard;
