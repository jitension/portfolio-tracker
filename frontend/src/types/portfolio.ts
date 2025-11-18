/**
 * Portfolio & Holdings Type Definitions
 * Matches the Django API response structure
 */

export interface Portfolio {
  total_value: number;
  total_equity: number;
  cash: number;
  buying_power: number;
  total_pl: number;
  total_pl_percent: number;
  daily_pl: number;
  daily_pl_percent: number;
  stocks_value: number;
  options_value: number;
  crypto_value: number;
  holdings_count: number;
  stocks_count: number;
  options_count: number;
  crypto_count: number;
  market_status: 'open' | 'closed' | 'extended';
  last_updated: string; // ISO datetime string
}

export interface Holding {
  id: string;
  symbol: string;
  asset_type: 'stock' | 'option' | 'crypto';
  quantity: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  total_pl: number;
  total_pl_percent: number;
  daily_pl: number;
  daily_pl_percent: number;
  company_name: string | null;
  sector: string | null;
  last_updated: string; // ISO datetime string
  // Option-specific fields
  option_type?: 'call' | 'put';
  strike_price?: number;
  expiration_date?: string;
  contracts?: number;
}

export interface PortfolioSnapshot {
  timestamp: string;
  total_value: number;
  total_pl: number;
  total_pl_percent: number;
  daily_pl: number;
  daily_pl_percent: number;
}

export interface SyncResponse {
  status: string;
  message?: string;
  synced_at: string;
  portfolio?: Portfolio;
  holdings_created?: number;
  holdings_updated?: number;
  total_holdings?: number;
}

// Computed/derived types for display
export interface HoldingWithAllocation extends Holding {
  allocation_percent: number; // Calculated: (market_value / portfolio_total_value) * 100
}

export interface PortfolioMetrics {
  winners: number; // Count of positive P/L holdings
  losers: number; // Count of negative P/L holdings
  top_performer: Holding | null;
  worst_performer: Holding | null;
  average_return: number;
}

// NEW TYPES FOR ENHANCED DASHBOARD

export interface InvestmentMetrics {
  cash_invested: number;
  margin_invested: number;
  total_invested: number;
  margin_available: number;
  leverage_percent: number;
  is_margin_account: boolean;
  message: string;
}

export interface PnLMetrics {
  ytd_pnl: number;
  ytd_pnl_percent: number;
  has_ytd_baseline: boolean;
  ytd_baseline_date: string | null;
  today_pnl: number;
  today_pnl_percent: number;
  is_market_open: boolean;
  ytd_message: string;
  today_message: string;
}

export interface TopMover {
  symbol: string;
  company_name: string;
  asset_type: 'stock' | 'option' | 'crypto';
  current_price: number;
  previous_close: number;
  price_change: number;
  percent_change: number;
  dollar_change: number;
  market_value: number;
  quantity: number;
}

export interface TopHolding {
  symbol: string;
  company_name: string;
  market_value: number;
  allocation_percent: number;
  quantity: number;
  asset_type: string;
}

export interface HoldingsAnalytics {
  total_holdings: number;
  stocks_count: number;
  options_count: number;
  crypto_count: number;
  top_holding: TopHolding | null;
  top_winner_percent: TopMover | null;
  top_loser_percent: TopMover | null;
  top_winner_dollar: TopMover | null;
  top_loser_dollar: TopMover | null;
  holdings_analyzed: number;
}

export interface HistoricalDataPoint {
  timestamp: string; // ISO datetime string
  value: number;
  change?: number;
  change_percent?: number;
}

export interface AllocationData {
  symbol: string;
  company_name: string;
  asset_type: string;
  market_value: number;
  allocation_percent: number;
  quantity: number;
}
