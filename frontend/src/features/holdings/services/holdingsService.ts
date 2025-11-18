/**
 * Holdings Service
 * API calls for holdings data
 */
import api from '../../../services/api';
import type { Holding, HoldingsResponse, HoldingsFilters } from '../../../types/holdings';

class HoldingsService {
  /**
   * Get all holdings with optional filters
   */
  async getHoldings(filters?: HoldingsFilters): Promise<HoldingsResponse> {
    const params: Record<string, any> = {};
    
    if (filters?.asset_type && filters.asset_type !== 'all') {
      params.asset_type = filters.asset_type;
    }
    if (filters?.sort) {
      params.sort = filters.sort;
    }
    if (filters?.page) {
      params.page = filters.page;
    }
    if (filters?.page_size) {
      params.page_size = filters.page_size;
    }

    const response = await api.get('portfolio/holdings/', { params });
    // Extract data from Django wrapper: { success: true, data: { holdings: [...], count: N } }
    return response.data.data as HoldingsResponse;
  }

  /**
   * Get specific holding by symbol
   */
  async getHoldingBySymbol(symbol: string): Promise<Holding> {
    const response = await api.get(`portfolio/holdings/${symbol}/`);
    // Extract data from Django wrapper: { success: true, data: {...} }
    return response.data.data as Holding;
  }
}

export const holdingsService = new HoldingsService();
