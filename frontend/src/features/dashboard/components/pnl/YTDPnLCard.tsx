/**
 * YTD P&L Card
 * Displays Year-to-Date profit/loss
 */
import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';

interface YTDPnLCardProps {
  ytdPnL: number;
  ytdPnLPercent: number;
  hasBaseline: boolean;
  message: string;
}

const YTDPnLCard: React.FC<YTDPnLCardProps> = ({ 
  ytdPnL, 
  ytdPnLPercent, 
  hasBaseline,
  message 
}) => {
  const isPositive = ytdPnL >= 0;
  const Icon = isPositive ? TrendingUp : TrendingDown;
  const color = isPositive ? 'success.main' : 'error.main';

  return (
    <Card variant="outlined" sx={{ height: '100%', flexGrow: 1 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Icon sx={{ mr: 1, color }} />
          <Typography variant="body2" color="text.secondary">
            P/L Year-to-Date
          </Typography>
        </Box>
        <Typography variant="h4" component="div" color={color}>
          {isPositive ? '+' : ''}${Math.abs(ytdPnL).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Typography>
        <Typography variant="h6" color={color} sx={{ mt: 0.5 }}>
          {isPositive ? '+' : ''}{ytdPnLPercent.toFixed(2)}%
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {hasBaseline ? message : 'Insufficient historical data'}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default YTDPnLCard;
