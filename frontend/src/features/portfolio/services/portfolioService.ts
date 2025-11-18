/**
 * Portfolio Service
 * Handles API calls for portfolio operations
 */
import apiClient from '../../../services/api';
import type { ApiResponse } from '../../../types/api';
import type { 
  Portfolio, 
  SyncResponse,
  InvestmentMetrics,
  PnLMetrics,
  HoldingsAnalytics,
  HistoricalDataPoint,
  AllocationData
} from '../../../types/portfolio';

export const portfolioService = {
  /**
   * Get portfolio summary
   */
  getSummary: async (): Promise<Portfolio> => {
    const response = await apiClient.get<ApiResponse<Portfolio>>('/portfolio/summary/');
    return response.data.data!;
  },

  /**
   * Sync portfolio data from Robinhood
   */
  syncPortfolio: async (): Promise<SyncResponse> => {
    const response = await apiClient.post<ApiResponse<SyncResponse>>('/portfolio/sync/', {});
    return response.data.data!;
  },

  /**
   * Get investment overview (margin & leverage metrics)
   */
  getInvestmentOverview: async (): Promise<InvestmentMetrics> => {
    const response = await apiClient.get<ApiResponse<InvestmentMetrics>>('/portfolio/investment-overview/');
    return response.data.data!;
  },

  /**
   * Get P&L metrics (YTD and today)
   */
  getPnLMetrics: async (): Promise<PnLMetrics> => {
    const response = await apiClient.get<ApiResponse<PnLMetrics>>('/portfolio/pnl-metrics/');
    return response.data.data!;
  },

  /**
   * Get holdings analytics (top movers and concentration)
   */
  getHoldingsAnalytics: async (): Promise<HoldingsAnalytics> => {
    const response = await apiClient.get<ApiResponse<HoldingsAnalytics>>('/portfolio/holdings-analytics/');
    return response.data.data!;
  },

  /**
   * Get historical portfolio data for charts
   * @param period Time period (1D, 1W, 1M, 1Y, YTD, All)
   */
  getHistoricalData: async (period: string = '1M'): Promise<HistoricalDataPoint[]> => {
    const response = await apiClient.get<ApiResponse<{ data_points: HistoricalDataPoint[] }>>(
      `/portfolio/historical/?period=${period}`
    );
    return response.data.data!.data_points;
  },

  /**
   * Get portfolio allocation data for pie chart
   */
  getAllocationData: async (): Promise<AllocationData[]> => {
    const response = await apiClient.get<ApiResponse<{ allocations: AllocationData[] }>>(
      '/portfolio/allocation/'
    );
    return response.data.data!.allocations;
  },
};
