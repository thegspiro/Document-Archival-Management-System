/**
 * Vocabulary management page. Browse domains and manage terms within each.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { vocabularyApi } from '../api/vocabulary';
import type { VocabularyDomain, VocabularyTerm } from '../api/vocabulary';
import Spinner from '../components/ui/Spinner';

export default function VocabularyPage() {
  const queryClient = useQueryClient();
  const [selectedDomainId, setSelectedDomainId] = useState<number | null>(null);
  const [newTerm, setNewTerm] = useState('');

  const domainsQuery = useQuery<VocabularyDomain[]>({
    queryKey: ['vocabulary', 'domains'],
    queryFn: () => vocabularyApi.listDomains(),
  });

  const termsQuery = useQuery<VocabularyTerm[]>({
    queryKey: ['vocabulary', 'terms', selectedDomainId],
    queryFn: () => vocabularyApi.getTerms(selectedDomainId!),
    enabled: selectedDomainId != null,
  });

  const createTermMutation = useMutation({
    mutationFn: () => vocabularyApi.createTerm(selectedDomainId!, { term: newTerm.trim() }),
    onSuccess: () => {
      setNewTerm('');
      queryClient.invalidateQueries({ queryKey: ['vocabulary', 'terms', selectedDomainId] });
    },
  });

  const deleteTermMutation = useMutation({
    mutationFn: (termId: number) => vocabularyApi.deleteTerm(termId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['vocabulary', 'terms', selectedDomainId] }),
  });

  const handleAddTerm = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTerm.trim() || selectedDomainId == null) return;
    createTermMutation.mutate();
  };

  const selectedDomain = domainsQuery.data?.find((d) => d.id === selectedDomainId);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Controlled Vocabulary</h1>

      <div className="flex gap-6">
        {/* Domain list */}
        <aside className="w-64 min-w-[256px]" aria-label="Vocabulary domains">
          <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-3">Domains</h2>
          {domainsQuery.isLoading && <Spinner size="sm" label="Loading domains" />}
          {domainsQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load domains.</p>}
          {domainsQuery.data && (
            <ul className="space-y-1">
              {domainsQuery.data.map((domain) => (
                <li key={domain.id}>
                  <button type="button" onClick={() => setSelectedDomainId(domain.id)}
                    className={`w-full text-left px-3 py-2 rounded text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] ${
                      selectedDomainId === domain.id
                        ? 'bg-blue-50 dark:bg-blue-900/30 font-medium text-blue-700 dark:text-blue-400'
                        : 'text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-700'
                    }`}>
                    {domain.name.replace(/_/g, ' ')}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </aside>

        {/* Terms panel */}
        <main className="flex-1">
          {selectedDomainId == null && (
            <p className="text-gray-500 dark:text-gray-400 py-8">Select a domain to view and manage its terms.</p>
          )}

          {selectedDomain && (
            <>
              <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-1">{selectedDomain.name.replace(/_/g, ' ')}</h2>
              {selectedDomain.description && <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">{selectedDomain.description}</p>}

              {selectedDomain.allows_user_addition && (
                <form onSubmit={handleAddTerm} className="mb-4 flex gap-2">
                  <label htmlFor="new-term" className="sr-only">New term</label>
                  <input id="new-term" type="text" value={newTerm} onChange={(e) => setNewTerm(e.target.value)}
                    placeholder="Add a new term..."
                    className="min-h-[44px] flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
                  <button type="submit" disabled={!newTerm.trim() || createTermMutation.isPending}
                    className="min-h-[44px] px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
                    {createTermMutation.isPending ? 'Adding...' : 'Add Term'}
                  </button>
                </form>
              )}

              {termsQuery.isLoading && <Spinner size="sm" label="Loading terms" />}
              {termsQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load terms.</p>}
              {termsQuery.data && termsQuery.data.length === 0 && (
                <p className="text-gray-500 dark:text-gray-400 text-sm">No terms in this domain yet.</p>
              )}
              {termsQuery.data && termsQuery.data.length > 0 && (
                <ul className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
                  {termsQuery.data.map((term) => (
                    <li key={term.id} className="px-4 py-3 flex items-center justify-between">
                      <div>
                        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{term.term}</p>
                        {term.definition && <p className="text-xs text-gray-500 dark:text-gray-400">{term.definition}</p>}
                      </div>
                      <button type="button" onClick={() => deleteTermMutation.mutate(term.id)}
                        aria-label={`Delete term: ${term.term}`}
                        className="min-h-[44px] min-w-[44px] flex items-center justify-center text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]">
                        <span aria-hidden="true">&times;</span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
            </>
          )}
        </main>
      </div>
    </div>
  );
}
