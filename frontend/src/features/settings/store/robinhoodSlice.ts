/**
 * Redux Slice for Robinhood Account Management
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import type { PayloadAction } from '@reduxjs/toolkit';
import type { RobinhoodAccount, LinkRobinhoodAccountRequest } from '../types';
import * as robinhoodService from '../services/robinhoodService';

interface RobinhoodState {
  accounts: RobinhoodAccount[];
  isLoading: boolean;
  isLinking: boolean;
  error: string | null;
  linkingError: string | null;
  mfaRequired: boolean;
  mfaType: 'sms' | 'app' | null;
}

const initialState: RobinhoodState = {
  accounts: [],
  isLoading: false,
  isLinking: false,
  error: null,
  linkingError: null,
  mfaRequired: false,
  mfaType: null,
};

/**
 * Fetch all Robinhood accounts
 */
export const fetchAccounts = createAsyncThunk(
  'robinhood/fetchAccounts',
  async (_, { rejectWithValue }) => {
    try {
      const accounts = await robinhoodService.fetchRobinhoodAccounts();
      return accounts;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || error.message);
    }
  }
);

/**
 * Link a new Robinhood account
 */
export const linkAccount = createAsyncThunk(
  'robinhood/linkAccount',
  async (credentials: LinkRobinhoodAccountRequest, { rejectWithValue }) => {
    try {
      const account = await robinhoodService.linkRobinhoodAccount(credentials);
      return account;
    } catch (error: any) {
      if (error.mfaRequired) {
        return rejectWithValue({
          message: error.message,
          mfaRequired: true,
          mfaType: error.mfaType,
        });
      }
      return rejectWithValue({
        message: error.response?.data?.error?.message || error.message,
        mfaRequired: false,
      });
    }
  }
);

/**
 * Unlink a Robinhood account
 */
export const unlinkAccount = createAsyncThunk(
  'robinhood/unlinkAccount',
  async (accountId: string, { rejectWithValue }) => {
    try {
      await robinhoodService.unlinkRobinhoodAccount(accountId);
      return accountId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || error.message);
    }
  }
);

/**
 * Test connection to a Robinhood account
 */
export const testAccountConnection = createAsyncThunk(
  'robinhood/testConnection',
  async ({ accountId, mfaCode }: { accountId: string; mfaCode?: string }, { rejectWithValue }) => {
    try {
      await robinhoodService.testConnection(accountId, mfaCode ? { mfa_code: mfaCode } : undefined);
      return accountId;
    } catch (error: any) {
      return rejectWithValue(error.response?.data?.error?.message || error.message);
    }
  }
);

const robinhoodSlice = createSlice({
  name: 'robinhood',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
      state.linkingError = null;
    },
    clearMfaRequired: (state) => {
      state.mfaRequired = false;
      state.mfaType = null;
      state.linkingError = null;
    },
  },
  extraReducers: (builder) => {
    builder
      // Fetch accounts
      .addCase(fetchAccounts.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(fetchAccounts.fulfilled, (state, action: PayloadAction<RobinhoodAccount[]>) => {
        state.isLoading = false;
        state.accounts = action.payload;
      })
      .addCase(fetchAccounts.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Link account
      .addCase(linkAccount.pending, (state) => {
        state.isLinking = true;
        state.linkingError = null;
        state.mfaRequired = false;
      })
      .addCase(linkAccount.fulfilled, (state, action: PayloadAction<RobinhoodAccount>) => {
        state.isLinking = false;
        state.accounts.push(action.payload);
        state.mfaRequired = false;
        state.mfaType = null;
      })
      .addCase(linkAccount.rejected, (state, action) => {
        state.isLinking = false;
        const payload = action.payload as any;
        state.linkingError = payload.message;
        state.mfaRequired = payload.mfaRequired || false;
        state.mfaType = payload.mfaType || null;
      })
      
      // Unlink account
      .addCase(unlinkAccount.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(unlinkAccount.fulfilled, (state, action: PayloadAction<string>) => {
        state.isLoading = false;
        state.accounts = state.accounts.filter(account => account.id !== action.payload);
      })
      .addCase(unlinkAccount.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      
      // Test connection
      .addCase(testAccountConnection.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(testAccountConnection.fulfilled, (state, action: PayloadAction<string>) => {
        state.isLoading = false;
        // Update account sync status
        const account = state.accounts.find(acc => acc.id === action.payload);
        if (account) {
          account.sync_status = 'success';
          account.last_sync = new Date().toISOString();
        }
      })
      .addCase(testAccountConnection.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError, clearMfaRequired } = robinhoodSlice.actions;
export default robinhoodSlice.reducer;
