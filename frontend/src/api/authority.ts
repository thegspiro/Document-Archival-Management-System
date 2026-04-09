/** Authority record API calls. */
import apiClient from './client';
import type { AuthorityRecord, PaginatedResponse } from '../types/api';

export const authorityApi = {
  list: (params?: Record<string, string | number>) =>
    apiClient.get<PaginatedResponse<AuthorityRecord>>('/authority', { params }).then((r) => r.data),

  get: (id: number) =>
    apiClient.get<AuthorityRecord>(`/authority/${id}`).then((r) => r.data),

  create: (data: Partial<AuthorityRecord>) =>
    apiClient.post<AuthorityRecord>('/authority', data).then((r) => r.data),

  update: (id: number, data: Partial<AuthorityRecord>) =>
    apiClient.patch<AuthorityRecord>(`/authority/${id}`, data).then((r) => r.data),

  delete: (id: number) =>
    apiClient.delete(`/authority/${id}`),

  getDocuments: (id: number) =>
    apiClient.get(`/authority/${id}/documents`).then((r) => r.data),

  linkWikidata: (id: number, qid: string) =>
    apiClient.post(`/authority/${id}/wikidata/link`, { qid }).then((r) => r.data),

  unlinkWikidata: (id: number) =>
    apiClient.delete(`/authority/${id}/wikidata/link`),
};
