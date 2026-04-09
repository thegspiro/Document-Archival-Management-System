/** Vocabulary API calls. */
import apiClient from './client';

export interface VocabularyDomain {
  id: number;
  name: string;
  description: string | null;
  allows_user_addition: boolean;
}

export interface VocabularyTerm {
  id: number;
  domain_id: number;
  term: string;
  definition: string | null;
  broader_term_id: number | null;
  is_active: boolean;
  sort_order: number;
}

export const vocabularyApi = {
  listDomains: () =>
    apiClient.get<VocabularyDomain[]>('/vocabulary/domains').then((r) => r.data),

  getTerms: (domainId: number) =>
    apiClient.get<VocabularyTerm[]>(`/vocabulary/domains/${domainId}/terms`).then((r) => r.data),

  createTerm: (domainId: number, data: { term: string; definition?: string }) =>
    apiClient.post<VocabularyTerm>(`/vocabulary/domains/${domainId}/terms`, data).then((r) => r.data),

  updateTerm: (id: number, data: Partial<VocabularyTerm>) =>
    apiClient.patch<VocabularyTerm>(`/vocabulary/terms/${id}`, data).then((r) => r.data),

  deleteTerm: (id: number) =>
    apiClient.delete(`/vocabulary/terms/${id}`),

  mergeTerm: (id: number, intoTermId: number) =>
    apiClient.post(`/vocabulary/terms/${id}/merge`, { into_term_id: intoTermId }).then((r) => r.data),
};
