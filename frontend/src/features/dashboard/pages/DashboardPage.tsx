/**
 * Dashboard Page
 * Main landing page showing enhanced portfolio dashboard
 */
import { useState, useEffect } from 'react';
import { Box, Divider, Typography, CircularProgress } from '@mui/material';
import InvestmentOverview from '../components/investment/InvestmentOverview';
import PnLMetrics from '../components/pnl/PnLMetrics';
import HoldingsAnalytics from '../components/analytics/HoldingsAnalytics';
import PortfolioLineChart from '../components/charts/PortfolioLineChart';
import AllocationPieChart from '../components/charts/AllocationPieChart';
import { useAppDispatch, useAppSelector } from '../../../store';
import { fetchHistoricalData, fetchAllocationData } from '../../portfolio/store/portfolioSlice';

export const DashboardPage = () => {
  const dispatch = useAppDispatch();
  const [selectedPeriod, setSelectedPeriod] = useState('1M');
  
  const { 
    historicalData, 
    allocationData, 
    isLoadingHistorical, 
    isLoadingAllocation
  } = useAppSelector((state) => state.portfolio);

  useEffect(() => {
    dispatch(fetchHistoricalData(selectedPeriod));
    dispatch(fetchAllocationData());
  }, [dispatch, selectedPeriod]);

  const handlePeriodChange = (period: string) => {
    setSelectedPeriod(period);
    dispatch(fetchHistoricalData(period));
  };

  return (
    <Box sx={{ width: '100%' }}>
      {/* Investment Overview - Margin & Leverage Metrics */}
      <InvestmentOverview />
      
      <Divider sx={{ my: 2.5 }} />
      
      {/* P&L Metrics - YTD and Today */}
      <PnLMetrics />
      
      <Divider sx={{ my: 2.5 }} />
      
      {/* Holdings Analytics - Top Movers and Concentration */}
      <HoldingsAnalytics />
      
      <Divider sx={{ my: 2.5 }} />
      
      {/* Portfolio Allocation - Main Section (Full Width) */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
          Portfolio Allocation
        </Typography>
        {isLoadingAllocation ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <AllocationPieChart data={allocationData} />
        )}
      </Box>
      
      <Divider sx={{ my: 2.5 }} />
      
      {/* Portfolio Performance (Full Width) */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="h6" sx={{ mb: 2 }}>
          Portfolio Performance
        </Typography>
        {isLoadingHistorical ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
            <CircularProgress />
          </Box>
        ) : (
          <PortfolioLineChart
            data={historicalData}
            selectedPeriod={selectedPeriod}
            onPeriodChange={handlePeriodChange}
          />
        )}
      </Box>
    </Box>
  );
};

export default DashboardPage;
