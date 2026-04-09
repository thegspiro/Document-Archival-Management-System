/**
 * Full-text search page with faceted filters for documents.
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import apiClient from '../api/client';
import Spinner from '../components/ui/Spinner';
import type { Document, PaginatedResponse } from '../types/api';

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get('q') ?? '';
  const page = Number(searchParams.get('page') ?? '1');
  const dateFrom = searchParams.get('date_from') ?? '';
  const dateTo = searchParams.get('date_to') ?? '';
  const isPublic = searchParams.get('is_public') ?? '';

  const [localQuery, setLocalQuery] = useState(q);

  const { data, isLoading, isError } = useQuery<PaginatedResponse<Document>>({
    queryKey: ['search', q, page, dateFrom, dateTo, isPublic],
    queryFn: () => apiClient.get('/search', {
      params: {
        ...(q ? { q } : {}),
        page,
        per_page: 25,
        ...(dateFrom ? { date_from: dateFrom } : {}),
        ...(dateTo ? { date_to: dateTo } : {}),
        ...(isPublic ? { is_public: isPublic === 'true' } : {}),
      },
    }).then((r) => r.data),
    enabled: q.length > 0 || dateFrom.length > 0 || dateTo.length > 0,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const next = new URLSearchParams(searchParams);
    if (localQuery.trim()) { next.set('q', localQuery.trim()); } else { next.delete('q'); }
    next.set('page', '1');
    setSearchParams(next);
  };

  const updateFilter = (key: string, value: string) => {
    const next = new URLSearchParams(searchParams);
    if (value) { next.set(key, value); } else { next.delete(key); }
    next.set('page', '1');
    setSearchParams(next);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Search</h1>

      <form onSubmit={handleSearch} className="mb-6" role="search" aria-label="Search documents">
        <div className="flex gap-2">
          <label htmlFor="search-input" className="sr-only">Search query</label>
          <input id="search-input" type="search" value={localQuery} onChange={(e) => setLocalQuery(e.target.value)}
            placeholder="Search documents by title, content, notes..."
            className="min-h-[44px] flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
          <button type="submit"
            className="min-h-[44px] px-6 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
            Search
          </button>
        </div>
      </form>

      {/* Filters */}
      <div className="mb-6 flex flex-wrap items-end gap-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700" role="group" aria-label="Search filters">
        <div>
          <label htmlFor="filter-date-from" className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Date from</label>
          <input id="filter-date-from" type="date" value={dateFrom} onChange={(e) => updateFilter('date_from', e.target.value)}
            className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
        </div>
        <div>
          <label htmlFor="filter-date-to" className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Date to</label>
          <input id="filter-date-to" type="date" value={dateTo} onChange={(e) => updateFilter('date_to', e.target.value)}
            className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
        </div>
        <div>
          <label htmlFor="filter-public" className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Visibility</label>
          <select id="filter-public" value={isPublic} onChange={(e) => updateFilter('is_public', e.target.value)}
            className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]">
            <option value="">All</option>
            <option value="true">Public only</option>
            <option value="false">Private only</option>
          </select>
        </div>
      </div>

      {/* Results */}
      {!q && !dateFrom && !dateTo && (
        <p className="text-gray-500 dark:text-gray-400 text-center py-16">Enter a search query or apply filters to find documents.</p>
      )}

      {isLoading && <div className="flex items-center justify-center py-16"><Spinner label="Searching" /></div>}
      {isError && <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Search failed. Please try again.</div>}

      {data && data.items.length === 0 && (q || dateFrom || dateTo) && (
        <p className="text-gray-500 dark:text-gray-400 text-center py-16">No documents match your search.</p>
      )}

      {data && data.items.length > 0 && (
        <>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{data.total} result{data.total !== 1 ? 's' : ''} found</p>
          <ul className="space-y-3">
            {data.items.map((doc) => (
              <li key={doc.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <Link to={`/archive/documents/${doc.id}`}
                  className="text-blue-700 dark:text-blue-400 hover:underline font-semibold text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                  {doc.title}
                </Link>
                <div className="mt-1 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                  {doc.accession_number && <span>{doc.accession_number}</span>}
                  {doc.date_display && <span>{doc.date_display}</span>}
                  {doc.creator && <span>by {doc.creator.authorized_name}</span>}
                </div>
                {doc.scope_and_content && (
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{doc.scope_and_content}</p>
                )}
              </li>
            ))}
          </ul>

          {data.pages > 1 && (
            <nav aria-label="Search results pagination" className="mt-6 flex items-center justify-center gap-2">
              <button type="button" disabled={page <= 1} onClick={() => { const p = new URLSearchParams(searchParams); p.set('page', String(page - 1)); setSearchParams(p); }}
                className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Previous page">Previous</button>
              <span className="text-sm text-gray-600 dark:text-gray-400" aria-current="page">Page {data.page} of {data.pages}</span>
              <button type="button" disabled={page >= data.pages} onClick={() => { const p = new URLSearchParams(searchParams); p.set('page', String(page + 1)); setSearchParams(p); }}
                className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Next page">Next</button>
            </nav>
          )}
        </>
      )}
    </div>
  );
}
