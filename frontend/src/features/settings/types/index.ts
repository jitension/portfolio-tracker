/**
 * TypeScript types for Settings and Robinhood integration
 */

export interface RobinhoodAccount {
  id: string;
  user_id: number;
  account_number: string;
  account_type: 'cash' | 'margin' | 'gold';
  mfa_enabled: boolean;
  mfa_type: 'sms' | 'app';
  last_sync: string | null;
  sync_status: 'never_synced' | 'success' | 'pending' | 'failed';
  sync_error: string | null;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface LinkRobinhoodAccountRequest {
  username: string;
  password: string;
  mfa_code?: string;
  mfa_type?: 'sms' | 'app';
}

export interface LinkRobinhoodAccountResponse {
  success: boolean;
  data?: {
    account: RobinhoodAccount;
    message: string;
  };
  error?: {
    code: string;
    message: string;
    details?: {
      mfa_required?: boolean;
      mfa_type?: string;
    };
  };
}

export interface TestConnectionRequest {
  mfa_code?: string;
}

export interface RobinhoodAccountsResponse {
  success: boolean;
  data?: {
    accounts: RobinhoodAccount[];
    count: number;
  };
  error?: {
    code: string;
    message: string;
    details?: any;
  };
}
