/**
 * Leverage Card
 * Displays portfolio leverage percentage with color-coded risk levels
 */
import React from 'react';
import { Card, CardContent, Typography, Box, Chip } from '@mui/material';
import { ShowChart } from '@mui/icons-material';

interface LeverageCardProps {
  leveragePercent: number;
  isMarginAccount: boolean;
  message: string;
}

const LeverageCard: React.FC<LeverageCardProps> = ({ 
  leveragePercent,
  message 
}) => {
  // Determine color based on leverage level
  const getRiskColor = () => {
    if (leveragePercent <= 100) return 'success';
    if (leveragePercent <= 150) return 'warning';
    if (leveragePercent <= 200) return 'error';
    return 'error';
  };

  const getRiskLabel = () => {
    if (leveragePercent <= 100) return 'No Risk';
    if (leveragePercent <= 150) return 'Moderate';
    if (leveragePercent <= 200) return 'High Risk';
    return 'Very High';
  };

  const riskColor = getRiskColor();
  const riskLabel = getRiskLabel();

  return (
    <Card variant="outlined" sx={{ height: '100%', flexGrow: 1 }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <ShowChart sx={{ mr: 1, color: `${riskColor}.main` }} />
            <Typography variant="body2" color="text.secondary">
              Portfolio Leverage
            </Typography>
          </Box>
          <Chip 
            label={riskLabel} 
            size="small" 
            color={riskColor}
          />
        </Box>
        <Typography 
          variant="h4" 
          component="div"
          color={`${riskColor}.main`}
        >
          {leveragePercent.toFixed(1)}%
        </Typography>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          {message}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default LeverageCard;
