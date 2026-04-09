/** Event API calls. */
import apiClient from './client';
import type { Event, PaginatedResponse } from '../types/api';

export const eventsApi = {
  list: (params?: Record<string, string | number>) =>
    apiClient.get<PaginatedResponse<Event>>('/events', { params }).then((r) => r.data),

  get: (id: number) =>
    apiClient.get<Event>(`/events/${id}`).then((r) => r.data),

  create: (data: Partial<Event>) =>
    apiClient.post<Event>('/events', data).then((r) => r.data),

  update: (id: number, data: Partial<Event>) =>
    apiClient.patch<Event>(`/events/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete(`/events/${id}`),
};
