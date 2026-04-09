/** Exhibition API calls. */
import apiClient from './client';
import type { Exhibition, PaginatedResponse } from '../types/api';

export const exhibitionsApi = {
  list: (params?: Record<string, string | number>) =>
    apiClient.get<PaginatedResponse<Exhibition>>('/exhibitions', { params }).then((r) => r.data),

  get: (id: number) =>
    apiClient.get<Exhibition>(`/exhibitions/${id}`).then((r) => r.data),

  create: (data: Partial<Exhibition>) =>
    apiClient.post<Exhibition>('/exhibitions', data).then((r) => r.data),

  update: (id: number, data: Partial<Exhibition>) =>
    apiClient.patch<Exhibition>(`/exhibitions/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete(`/exhibitions/${id}`),

  getPages: (id: number) =>
    apiClient.get(`/exhibitions/${id}/pages`).then((r) => r.data),

  createPage: (id: number, data: Record<string, unknown>) =>
    apiClient.post(`/exhibitions/${id}/pages`, data).then((r) => r.data),
};
