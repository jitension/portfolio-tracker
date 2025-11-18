/**
 * Top Mover Card
 * Reusable component for displaying top winners/losers
 */
import React from 'react';
import { Card, CardContent, Typography, Box } from '@mui/material';
import { TrendingUp, TrendingDown } from '@mui/icons-material';
import type { TopMover } from '../../../../types/portfolio';

interface TopMoverCardProps {
  title: string;
  mover: TopMover;
  isWinner: boolean;
  sortBy: 'percent' | 'dollar';
}

const TopMoverCard: React.FC<TopMoverCardProps> = ({ 
  title, 
  mover, 
  isWinner
}) => {
  const Icon = isWinner ? TrendingUp : TrendingDown;
  const color = isWinner ? 'success.main' : 'error.main';
  const bgColor = isWinner ? 'success.dark' : 'error.dark';

  return (
    <Card 
      variant="outlined"
      sx={{ 
        height: '100%',
        flexGrow: 1,
        bgcolor: `${bgColor}`,
        backgroundImage: 'none',
      }}
    >
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
          <Icon sx={{ mr: 1, color }} />
          <Typography variant="caption" color="text.secondary">
            {title}
          </Typography>
        </Box>
        <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
          {mover.symbol}
        </Typography>
        <Typography 
          variant="caption" 
          color="text.secondary" 
          sx={{ display: 'block', mb: 1 }}
          noWrap
        >
          {mover.company_name}
        </Typography>
        <Typography variant="h6" color={color}>
          {mover.dollar_change >= 0 ? '+' : ''}${Math.abs(mover.dollar_change).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
        </Typography>
        <Typography variant="body2" color={color}>
          {mover.percent_change >= 0 ? '+' : ''}{mover.percent_change.toFixed(2)}%
        </Typography>
      </CardContent>
    </Card>
  );
};

export default TopMoverCard;
