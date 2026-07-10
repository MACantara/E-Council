import { api } from './axios';

export interface LoginCredentials {
  users_username_or_email: string;
  users_password: string;
}

export interface RegisterData {
  users_first_name: string;
  users_last_name: string;
  users_username: string;
  users_email: string;
  users_password: string;
  users_repeat_password: string;
  users_role: string;
  users_department_name: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface User {
  users_id: number;
  users_first_name: string;
  users_last_name: string;
  users_username: string;
  users_email: string;
  users_role: string;
  users_department_name: string;
  users_email_verified: number;
  users_student_organization?: number | null;
  users_student_organization_position?: string | null;
}

export const login = async (credentials: LoginCredentials): Promise<TokenResponse> => {
  const response = await api.post('/api/v1/auth/login', credentials);
  return response.data;
};

export const register = async (data: RegisterData): Promise<User> => {
  const response = await api.post('/api/v1/auth/register', data);
  return response.data;
};

export const logout = async (): Promise<void> => {
  await api.post('/api/v1/auth/logout');
};

export const refresh = async (refresh_token: string): Promise<TokenResponse> => {
  const response = await api.post('/api/v1/auth/refresh', { refresh_token });
  return response.data.data;
};

export const getMe = async (): Promise<User> => {
  const response = await api.get('/api/v1/account/me');
  return response.data;
};
