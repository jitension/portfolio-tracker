/**
 * Portfolio Redux Slice
 * Manages portfolio state and data
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import { portfolioService } from '../services/portfolioService';
import type { 
  Portfolio,
  InvestmentMetrics,
  PnLMetrics,
  HoldingsAnalytics,
  HistoricalDataPoint,
  AllocationData
} from '../../../types/portfolio';

interface PortfolioState {
  summary: Portfolio | null;
  investmentMetrics: InvestmentMetrics | null;
  pnlMetrics: PnLMetrics | null;
  holdingsAnalytics: HoldingsAnalytics | null;
  historicalData: HistoricalDataPoint[];
  allocationData: AllocationData[];
  isLoading: boolean;
  isLoadingInvestment: boolean;
  isLoadingPnL: boolean;
  isLoadingAnalytics: boolean;
  isLoadingHistorical: boolean;
  isLoadingAllocation: boolean;
  error: string | null;
  lastSynced: string | null;
}

const initialState: PortfolioState = {
  summary: null,
  investmentMetrics: null,
  pnlMetrics: null,
  holdingsAnalytics: null,
  historicalData: [],
  allocationData: [],
  isLoading: false,
  isLoadingInvestment: false,
  isLoadingPnL: false,
  isLoadingAnalytics: false,
  isLoadingHistorical: false,
  isLoadingAllocation: false,
  error: null,
  lastSynced: null,
};

// Async thunks
export const fetchPortfolioSummary = createAsyncThunk(
  'portfolio/fetchSummary',
  async (_, { rejectWithValue }) => {
    try {
      const summary = await portfolioService.getSummary();
      return summary;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch portfolio');
    }
  }
);

export const syncPortfolio = createAsyncThunk(
  'portfolio/sync',
  async (_, { rejectWithValue }) => {
    try {
      const result = await portfolioService.syncPortfolio();
      return result;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to sync portfolio');
    }
  }
);

// NEW ASYNC THUNKS FOR ENHANCED DASHBOARD

export const fetchInvestmentMetrics = createAsyncThunk(
  'portfolio/fetchInvestmentMetrics',
  async (_, { rejectWithValue }) => {
    try {
      const metrics = await portfolioService.getInvestmentOverview();
      return metrics;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch investment metrics');
    }
  }
);

export const fetchPnLMetrics = createAsyncThunk(
  'portfolio/fetchPnLMetrics',
  async (_, { rejectWithValue }) => {
    try {
      const metrics = await portfolioService.getPnLMetrics();
      return metrics;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch P&L metrics');
    }
  }
);

export const fetchHoldingsAnalytics = createAsyncThunk(
  'portfolio/fetchHoldingsAnalytics',
  async (_, { rejectWithValue }) => {
    try {
      const analytics = await portfolioService.getHoldingsAnalytics();
      return analytics;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch holdings analytics');
    }
  }
);

export const fetchHistoricalData = createAsyncThunk(
  'portfolio/fetchHistoricalData',
  async (period: string = '1M', { rejectWithValue }) => {
    try {
      const data = await portfolioService.getHistoricalData(period);
      return data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch historical data');
    }
  }
);

export const fetchAllocationData = createAsyncThunk(
  'portfolio/fetchAllocationData',
  async (_, { rejectWithValue }) => {
    try {
      const data = await portfolioService.getAllocationData();
      return data;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch allocation data');
    }
  }
);

// Slice
const portfolioSlice = createSlice({
  name: 'portfolio',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch summary
    builder
      .addCase(fetchPortfolioSummary.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchPortfolioSummary.fulfilled, (state, action) => {
        state.isLoading = false;
        state.summary = action.payload;
        state.lastSynced = new Date().toISOString();
        state.error = null;
      })
      .addCase(fetchPortfolioSummary.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Sync portfolio
    builder
      .addCase(syncPortfolio.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(syncPortfolio.fulfilled, (state, action) => {
        state.isLoading = false;
        state.summary = action.payload.portfolio || state.summary;
        state.lastSynced = action.payload.synced_at;
        state.error = null;
      })
      .addCase(syncPortfolio.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch investment metrics
    builder
      .addCase(fetchInvestmentMetrics.pending, (state) => {
        state.isLoadingInvestment = true;
      })
      .addCase(fetchInvestmentMetrics.fulfilled, (state, action) => {
        state.isLoadingInvestment = false;
        state.investmentMetrics = action.payload;
      })
      .addCase(fetchInvestmentMetrics.rejected, (state, action) => {
        state.isLoadingInvestment = false;
        state.error = action.payload as string;
      });

    // Fetch P&L metrics
    builder
      .addCase(fetchPnLMetrics.pending, (state) => {
        state.isLoadingPnL = true;
      })
      .addCase(fetchPnLMetrics.fulfilled, (state, action) => {
        state.isLoadingPnL = false;
        state.pnlMetrics = action.payload;
      })
      .addCase(fetchPnLMetrics.rejected, (state, action) => {
        state.isLoadingPnL = false;
        state.error = action.payload as string;
      });

    // Fetch holdings analytics
    builder
      .addCase(fetchHoldingsAnalytics.pending, (state) => {
        state.isLoadingAnalytics = true;
      })
      .addCase(fetchHoldingsAnalytics.fulfilled, (state, action) => {
        state.isLoadingAnalytics = false;
        state.holdingsAnalytics = action.payload;
      })
      .addCase(fetchHoldingsAnalytics.rejected, (state, action) => {
        state.isLoadingAnalytics = false;
        state.error = action.payload as string;
      });

    // Fetch historical data
    builder
      .addCase(fetchHistoricalData.pending, (state) => {
        state.isLoadingHistorical = true;
      })
      .addCase(fetchHistoricalData.fulfilled, (state, action) => {
        state.isLoadingHistorical = false;
        state.historicalData = action.payload;
      })
      .addCase(fetchHistoricalData.rejected, (state, action) => {
        state.isLoadingHistorical = false;
        state.error = action.payload as string;
      });

    // Fetch allocation data
    builder
      .addCase(fetchAllocationData.pending, (state) => {
        state.isLoadingAllocation = true;
      })
      .addCase(fetchAllocationData.fulfilled, (state, action) => {
        state.isLoadingAllocation = false;
        state.allocationData = action.payload;
      })
      .addCase(fetchAllocationData.rejected, (state, action) => {
        state.isLoadingAllocation = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError } = portfolioSlice.actions;
export default portfolioSlice.reducer;
