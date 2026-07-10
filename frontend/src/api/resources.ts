import { api } from './axios';
import type { PaginatedResponse, SingleResponse, MessageResponse } from '@/types';

export interface Resource {
  [key: string]: unknown;
}

const isFileList = (value: unknown): value is FileList =>
  typeof FileList !== 'undefined' && value instanceof FileList;

const isFile = (value: unknown): value is File =>
  typeof File !== 'undefined' && value instanceof File;

const appendFiles = (form: FormData, key: string, value: unknown) => {
  if (isFile(value)) {
    form.append(key, value);
  } else if (isFileList(value)) {
    Array.from(value).forEach((file) => form.append(key, file));
  } else if (Array.isArray(value) && value.every(isFile)) {
    value.forEach((file) => form.append(key, file));
  }
};

const buildMultipartPayload = (data: Record<string, unknown>) => {
  const form = new FormData();
  const payload: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(data)) {
    if (isFile(value) || isFileList(value) || (Array.isArray(value) && value.every(isFile))) {
      appendFiles(form, key, value);
    } else {
      payload[key] = value;
    }
  }

  form.append('data', JSON.stringify(payload));
  return form;
};

export const fetchResources = async <T extends Resource>(
  endpoint: string,
  params?: Record<string, unknown>
): Promise<PaginatedResponse<T>> => {
  const response = await api.get(endpoint, { params });
  return response.data;
};

export const fetchResource = async <T extends Resource>(
  endpoint: string,
  id: number | string
): Promise<SingleResponse<T>> => {
  const response = await api.get(`${endpoint}/${id}`);
  return response.data;
};

export const createResource = async <T extends Resource>(
  endpoint: string,
  data: Record<string, unknown>
): Promise<SingleResponse<T>> => {
  const response = await api.post(endpoint, data);
  return response.data;
};

export const updateResource = async <T extends Resource>(
  endpoint: string,
  id: number | string,
  data: Record<string, unknown>
): Promise<SingleResponse<T>> => {
  const response = await api.put(`${endpoint}/${id}`, data);
  return response.data;
};

export const updateResourceStatus = async <T extends Resource>(
  endpoint: string,
  id: number | string,
  status: string
): Promise<SingleResponse<T>> => {
  const response = await api.put(`${endpoint}/${id}/status`, { status });
  return response.data;
};

export const createMultipartResource = async <T extends Resource>(
  endpoint: string,
  data: Record<string, unknown>
): Promise<SingleResponse<T>> => {
  const form = buildMultipartPayload(data);
  const response = await api.post(endpoint, form, { headers: { 'Content-Type': undefined } });
  return response.data;
};

export const updateMultipartResource = async <T extends Resource>(
  endpoint: string,
  id: number | string,
  data: Record<string, unknown>
): Promise<SingleResponse<T>> => {
  const form = buildMultipartPayload(data);
  const response = await api.put(`${endpoint}/${id}`, form, {
    headers: { 'Content-Type': undefined },
  });
  return response.data;
};

export const deleteResource = async (
  endpoint: string,
  id: number | string
): Promise<MessageResponse> => {
  const response = await api.delete(`${endpoint}/${id}`);
  return response.data;
};
