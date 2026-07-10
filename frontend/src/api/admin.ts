import { api } from './axios';
import type { User, AuditLog, PaginatedList } from '@/types';

export const fetchUsers = async (
  params?: Record<string, unknown>
): Promise<PaginatedList<User>> => {
  const response = await api.get('/api/v1/admin/users', { params });
  return response.data;
};

export const fetchAuditLogs = async (
  params?: Record<string, unknown>
): Promise<PaginatedList<AuditLog>> => {
  const response = await api.get('/api/v1/admin/audit-logs', { params });
  return response.data;
};

export const updateUserRole = async (userId: number, role: string): Promise<User> => {
  const response = await api.put(`/api/v1/admin/users/${userId}/role`, { users_role: role });
  return response.data;
};

export const activateUser = async (userId: number): Promise<User> => {
  const response = await api.put(`/api/v1/admin/users/${userId}/activate`);
  return response.data;
};

export const deactivateUser = async (userId: number): Promise<User> => {
  const response = await api.put(`/api/v1/admin/users/${userId}/deactivate`);
  return response.data;
};
