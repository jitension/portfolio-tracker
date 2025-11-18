/**
 * Holdings Redux Slice
 * Manages holdings state and data
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import { holdingsService } from '../services/holdingsService';
import type { Holding, HoldingsFilters } from '../../../types/holdings';

interface HoldingsState {
  holdings: Holding[];
  selectedHolding: Holding | null;
  isLoading: boolean;
  error: string | null;
  filters: HoldingsFilters;
  totalCount: number;
}

const initialState: HoldingsState = {
  holdings: [],
  selectedHolding: null,
  isLoading: false,
  error: null,
  filters: {
    asset_type: 'all',
    page: 1,
    page_size: 25,
  },
  totalCount: 0,
};

// Async thunks
export const fetchHoldings = createAsyncThunk(
  'holdings/fetchHoldings',
  async (filters: HoldingsFilters | undefined, { rejectWithValue }) => {
    try {
      const response = await holdingsService.getHoldings(filters);
      return response;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch holdings');
    }
  }
);

export const fetchHoldingDetail = createAsyncThunk(
  'holdings/fetchHoldingDetail',
  async (symbol: string, { rejectWithValue }) => {
    try {
      const holding = await holdingsService.getHoldingBySymbol(symbol);
      return holding;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || 'Failed to fetch holding details');
    }
  }
);

// Slice
const holdingsSlice = createSlice({
  name: 'holdings',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    setFilters: (state, action: PayloadAction<HoldingsFilters>) => {
      state.filters = { ...state.filters, ...action.payload };
    },
    clearSelectedHolding: (state) => {
      state.selectedHolding = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch holdings
    builder
      .addCase(fetchHoldings.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchHoldings.fulfilled, (state, action) => {
        state.isLoading = false;
        state.holdings = action.payload.holdings;
        state.totalCount = action.payload.count;
        state.error = null;
      })
      .addCase(fetchHoldings.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });

    // Fetch holding detail
    builder
      .addCase(fetchHoldingDetail.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchHoldingDetail.fulfilled, (state, action) => {
        state.isLoading = false;
        state.selectedHolding = action.payload;
        state.error = null;
      })
      .addCase(fetchHoldingDetail.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError, setFilters, clearSelectedHolding } = holdingsSlice.actions;
export default holdingsSlice.reducer;
