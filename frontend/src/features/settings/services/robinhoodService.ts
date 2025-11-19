/**
 * Robinhood API Service
 * Handles all API calls related to Robinhood account management
 */
import { apiClient } from '../../../services/api';
import type {
  RobinhoodAccount,
  LinkRobinhoodAccountRequest,
  LinkRobinhoodAccountResponse,
  TestConnectionRequest,
  RobinhoodAccountsResponse,
} from '../types';

const ROBINHOOD_BASE = '/robinhood/accounts';

/**
 * Fetch all linked Robinhood accounts for the current user
 */
export const fetchRobinhoodAccounts = async (): Promise<RobinhoodAccount[]> => {
  const response = await apiClient.get<RobinhoodAccountsResponse>(`${ROBINHOOD_BASE}/`);
  
  if (response.data.success && response.data.data) {
    return response.data.data.accounts;
  }
  
  throw new Error(response.data.error?.message || 'Failed to fetch accounts');
};

/**
 * Link a new Robinhood account
 */
export const linkRobinhoodAccount = async (
  credentials: LinkRobinhoodAccountRequest
): Promise<RobinhoodAccount> => {
  const response = await apiClient.post<LinkRobinhoodAccountResponse>(
    `${ROBINHOOD_BASE}/link-account/`,
    credentials
  );
  
  if (response.data.success && response.data.data) {
    return response.data.data.account;
  }
  
  // Handle MFA required error
  if (response.data.error?.details?.mfa_required) {
    const error: any = new Error(response.data.error.message);
    error.mfaRequired = true;
    error.mfaType = response.data.error.details.mfa_type;
    throw error;
  }
  
  throw new Error(response.data.error?.message || 'Failed to link account');
};

/**
 * Unlink (deactivate) a Robinhood account
 */
export const unlinkRobinhoodAccount = async (accountId: string): Promise<void> => {
  const response = await apiClient.delete(`${ROBINHOOD_BASE}/${accountId}/`);
  
  if (!response.data.success) {
    throw new Error(response.data.error?.message || 'Failed to unlink account');
  }
};

/**
 * Test connection to a Robinhood account
 */
export const testConnection = async (
  accountId: string,
  request?: TestConnectionRequest
): Promise<boolean> => {
  const response = await apiClient.post(
    `${ROBINHOOD_BASE}/${accountId}/test-connection/`,
    request || {}
  );
  
  if (response.data.success) {
    return true;
  }
  
  // Handle MFA required error
  if (response.data.error?.code === 'AUTH_004') {
    const error: any = new Error(response.data.error.message);
    error.mfaRequired = true;
    throw error;
  }
  
  throw new Error(response.data.error?.message || 'Connection test failed');
};
