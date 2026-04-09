/** Location API calls. */
import apiClient from './client';
import type { Location, PaginatedResponse } from '../types/api';

export const locationsApi = {
  list: (params?: Record<string, string | number>) =>
    apiClient.get<PaginatedResponse<Location>>('/locations', { params }).then((r) => r.data),

  get: (id: number) =>
    apiClient.get<Location>(`/locations/${id}`).then((r) => r.data),

  create: (data: Partial<Location>) =>
    apiClient.post<Location>('/locations', data).then((r) => r.data),

  update: (id: number, data: Partial<Location>) =>
    apiClient.patch<Location>(`/locations/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete(`/locations/${id}`),
};
