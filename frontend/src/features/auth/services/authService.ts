/**
 * Authentication Service
 * Handles API calls for authentication operations
 */
import apiClient from '../../../services/api';
import type { ApiResponse } from '../../../types/api';
import type { LoginRequest, RegisterRequest, LoginResponse, User } from '../../../types/auth';

export const authService = {
  /**
   * Login user
   */
  login: async (credentials: LoginRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<LoginResponse>(
      '/auth/login/',
      credentials
    );
    return response.data;
  },

  /**
   * Register new user
   */
  register: async (userData: RegisterRequest): Promise<LoginResponse> => {
    const response = await apiClient.post<ApiResponse<LoginResponse>>(
      '/auth/register/',
      userData
    );
    return response.data.data!;
  },

  /**
   * Logout user
   */
  logout: async (): Promise<void> => {
    await apiClient.post('/auth/logout/');
  },

  /**
   * Get current user info
   */
  getCurrentUser: async (): Promise<User> => {
    const response = await apiClient.get<ApiResponse<User>>('/auth/user/me/');
    return response.data.data!;
  },

  /**
   * Refresh access token
   */
  refreshToken: async (refreshToken: string): Promise<{ access: string }> => {
    const response = await apiClient.post<ApiResponse<{ access: string }>>(
      '/auth/refresh/',
      { refresh: refreshToken }
    );
    return response.data.data!;
  },
};
