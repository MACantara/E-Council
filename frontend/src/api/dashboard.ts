import { api } from './axios';
import type { DashboardStats } from '@/types';

export const fetchDashboardStats = async (): Promise<DashboardStats> => {
  const response = await api.get('/api/v1/admin/dashboard');
  return response.data;
};
