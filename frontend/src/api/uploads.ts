import { api } from './axios';
import type { SingleResponse, ImageItem } from '@/types';

export interface FileUploadResponse {
  file: ImageItem;
}

export const uploadProfilePicture = async (file: File): Promise<SingleResponse<unknown>> => {
  const form = new FormData();
  form.append('file', file);
  const response = await api.post('/api/v1/account/profile-picture', form, {
    headers: { 'Content-Type': undefined },
  });
  return response.data;
};

export const uploadSignature = async (file: File): Promise<SingleResponse<unknown>> => {
  const form = new FormData();
  form.append('file', file);
  const response = await api.post('/api/v1/account/signature', form, {
    headers: { 'Content-Type': undefined },
  });
  return response.data;
};

export type DocumentationFileType = 'evaluation_image' | 'attendance_image' | 'event_photo';

export const uploadDocumentationFile = async (
  docId: number | string,
  fileType: DocumentationFileType,
  file: File
): Promise<SingleResponse<FileUploadResponse>> => {
  const form = new FormData();
  form.append('file_type', fileType);
  form.append('file', file);
  const response = await api.post(`/api/v1/documentation/${docId}/files`, form, {
    headers: { 'Content-Type': undefined },
  });
  return response.data;
};

export interface TransactionPayload {
  transaction_name?: string;
  transaction_date?: string;
  unit_amount?: number;
  unit_price?: number;
  total?: number;
  category?: string;
  other_category?: string;
  type?: 'Income' | 'Expense';
}

export const createTransaction = async (
  eventId: number | string,
  payload: TransactionPayload,
  receipt?: File
): Promise<SingleResponse<unknown>> => {
  const form = new FormData();
  form.append('data', JSON.stringify(payload));
  if (receipt) {
    form.append('receipt', receipt);
  }
  const response = await api.post(`/api/v1/events/${eventId}/transactions`, form, {
    headers: { 'Content-Type': undefined },
  });
  return response.data;
};

export const updateTransaction = async (
  eventId: number | string,
  transactionId: number | string,
  payload: TransactionPayload,
  receipt?: File
): Promise<SingleResponse<unknown>> => {
  const form = new FormData();
  form.append('data', JSON.stringify(payload));
  if (receipt) {
    form.append('receipt', receipt);
  }
  const response = await api.put(`/api/v1/events/${eventId}/transactions/${transactionId}`, form, {
    headers: { 'Content-Type': undefined },
  });
  return response.data;
};
