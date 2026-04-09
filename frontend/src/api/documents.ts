/** Document API calls. */
import apiClient from './client';
import type { Document, DocumentCreate, DocumentUpdate, PaginatedResponse } from '../types/api';

export const documentsApi = {
  list: (params?: Record<string, string | number | boolean>) =>
    apiClient.get<PaginatedResponse<Document>>('/documents', { params }).then((r) => r.data),

  get: (id: number) =>
    apiClient.get<Document>(`/documents/${id}`).then((r) => r.data),

  create: (data: DocumentCreate) =>
    apiClient.post<Document>('/documents', data).then((r) => r.data),

  update: (id: number, data: DocumentUpdate) =>
    apiClient.patch<Document>(`/documents/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete(`/documents/${id}`),

  uploadFile: (id: number, file: File) => {
    const formData = new FormData();
    formData.append('file', file);
    return apiClient.post(`/documents/${id}/files`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    }).then((r) => r.data);
  },

  downloadFile: (id: number, fileId: number) =>
    apiClient.get(`/documents/${id}/files/${fileId}/download`, { responseType: 'blob' })
      .then((r) => r.data),

  cite: (id: number, format: string) =>
    apiClient.get<string>(`/documents/${id}/cite`, { params: { format } }).then((r) => r.data),

  exportDoc: (id: number, format: string) =>
    apiClient.get(`/documents/${id}/export`, { params: { format } }).then((r) => r.data),

  bulk: (data: { document_ids: number[]; action: Record<string, unknown> }) =>
    apiClient.post('/documents/bulk', data).then((r) => r.data),

  retryOcr: (id: number, fileId: number) =>
    apiClient.post(`/documents/${id}/files/${fileId}/retry-ocr`).then((r) => r.data),
};
