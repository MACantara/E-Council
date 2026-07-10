import { api } from './axios';
import type { PaginatedResponse, SingleResponse, MessageResponse } from '@/types';

export interface Resource {
  [key: string]: unknown;
}

export const fetchResources = async <T extends Resource>(endpoint: string, params?: Record<string, unknown>): Promise<PaginatedResponse<T>> => {
  const response = await api.get(endpoint, { params });
  return response.data;
};

export const fetchResource = async <T extends Resource>(endpoint: string, id: number | string): Promise<SingleResponse<T>> => {
  const response = await api.get(`${endpoint}/${id}`);
  return response.data;
};

export const createResource = async <T extends Resource>(endpoint: string, data: Record<string, unknown>): Promise<SingleResponse<T>> => {
  const response = await api.post(endpoint, data);
  return response.data;
};

export const updateResource = async <T extends Resource>(endpoint: string, id: number | string, data: Record<string, unknown>): Promise<SingleResponse<T>> => {
  const response = await api.put(`${endpoint}/${id}`, data);
  return response.data;
};

export const updateResourceStatus = async <T extends Resource>(endpoint: string, id: number | string, status: string): Promise<SingleResponse<T>> => {
  const response = await api.put(`${endpoint}/${id}/status`, { status });
  return response.data;
};

export const createMultipartResource = async <T extends Resource>(endpoint: string, data: Record<string, unknown>): Promise<SingleResponse<T>> => {
  const form = new FormData();
  form.append('data', JSON.stringify(data));
  const response = await api.post(endpoint, form, { headers: { 'Content-Type': undefined } });
  return response.data;
};

export const updateMultipartResource = async <T extends Resource>(endpoint: string, id: number | string, data: Record<string, unknown>): Promise<SingleResponse<T>> => {
  const form = new FormData();
  form.append('data', JSON.stringify(data));
  const response = await api.put(`${endpoint}/${id}`, form, { headers: { 'Content-Type': undefined } });
  return response.data;
};

export const deleteResource = async (endpoint: string, id: number | string): Promise<MessageResponse> => {
  const response = await api.delete(`${endpoint}/${id}`);
  return response.data;
};
