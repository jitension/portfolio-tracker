/**
 * TypeScript type definitions for Holdings
 */

export interface Holding {
  id: string;
  symbol: string;
  asset_type: 'stock' | 'option' | 'crypto';
  quantity: number | string;
  average_cost: number | string;
  current_price: number | string;
  market_value: number | string;
  total_pl: number | string;
  total_pl_percent: number | string;
  daily_pl: number | string;
  daily_pl_percent: number | string;
  company_name?: string;
  sector?: string;
  last_updated: string;
  created_at: string;
  
  // Option-specific fields
  option_type?: 'call' | 'put';
  strike_price?: number | string;
  expiration_date?: string;
  contracts?: number;
  delta?: number | string;
  gamma?: number | string;
  theta?: number | string;
  vega?: number | string;
}

export interface HoldingsResponse {
  holdings: Holding[];
  count: number;
}

export interface HoldingsFilters {
  asset_type?: 'stock' | 'option' | 'crypto' | 'all';
  sort?: string;
  page?: number;
  page_size?: number;
}
