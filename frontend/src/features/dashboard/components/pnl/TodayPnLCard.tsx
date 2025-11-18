/**
 * Today P&L Card
 * Displays today's profit/loss performance
 */
import React from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

interface TodayPnLCardProps {
  todayPnL: number;
  todayPnLPercent: number;
  isMarketOpen: boolean;
  message: string;
}

const TodayPnLCard: React.FC<TodayPnLCardProps> = ({ 
  todayPnL, 
  todayPnLPercent, 
  isMarketOpen,
  message 
}) => {
  const isPositive = todayPnL >= 0;
  const Icon = isPositive ? TrendingUp : TrendingDown;
  const color = isPositive ? 'success.main' : 'error.main';

  return (
    <Card variant="outlined" sx={{ height: '100%', flexGrow: 1 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Icon sx={{ mr: 1, color }} />
            <Typography variant="body2" color="text.secondary">
              P/L Today
            </Typography>
          </Box>
          <Chip 
            label={isMarketOpen ? 'Market Open' : 'Market Closed'} 
            size="small" 
            color={isMarketOpen ? 'success' : 'default'}
            variant="outlined"
          />
        </Box>
        <Typography variant="h4" component="div" color={color}>
          {isPositive ? '+' : ''}${Math.abs(todayPnL).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Typography>
        <Typography variant="h6" color={color} sx={{ mt: 0.5 }}>
          {isPositive ? '+' : ''}{todayPnLPercent.toFixed(2)}%
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {message}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default TodayPnLCard;
