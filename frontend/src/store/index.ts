/**
 * Redux Store Configuration
 * Configures the central Redux store with all feature slices
 */
import { configureStore } from '@reduxjs/toolkit';
import { useDispatch, useSelector } from 'react-redux';
import type { TypedUseSelectorHook } from 'react-redux';

// Feature slices
import authReducer from '../features/auth/store/authSlice';
import portfolioReducer from '../features/portfolio/store/portfolioSlice';
import holdingsReducer from '../features/holdings/store/holdingsSlice';
import robinhoodReducer from '../features/settings/store/robinhoodSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    portfolio: portfolioReducer,
    holdings: holdingsReducer,
    robinhood: robinhoodReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore these action types for date serialization
        ignoredActions: ['portfolio/setLastSync'],
      },
    }),
  devTools: import.meta.env.DEV,
});

// Infer the `RootState` and `AppDispatch` types from the store itself
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

// Typed hooks for use throughout the app
export const useAppDispatch = () => useDispatch<AppDispatch>();
export const useAppSelector: TypedUseSelectorHook<RootState> = useSelector;
