/**
 * Public search page with full-text search and faceted filtering.
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import type { Document, PaginatedResponse } from '../../types/api';

export default function PublicSearchPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const q = searchParams.get('q') ?? '';
  const page = Number(searchParams.get('page') ?? '1');
  const dateFrom = searchParams.get('date_from') ?? '';
  const dateTo = searchParams.get('date_to') ?? '';

  const [localQuery, setLocalQuery] = useState(q);

  const hasQuery = q.length > 0 || dateFrom.length > 0 || dateTo.length > 0;

  const { data, isLoading, isError } = useQuery<PaginatedResponse<Document>>({
    queryKey: ['public', 'search', q, page, dateFrom, dateTo],
    queryFn: () => apiClient.get('/public/search', {
      params: {
        ...(q ? { q } : {}),
        page,
        per_page: 25,
        ...(dateFrom ? { date_from: dateFrom } : {}),
        ...(dateTo ? { date_to: dateTo } : {}),
      },
    }).then((r) => r.data),
    enabled: hasQuery,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    const next = new URLSearchParams(searchParams);
    if (localQuery.trim()) { next.set('q', localQuery.trim()); } else { next.delete('q'); }
    next.set('page', '1');
    setSearchParams(next);
  };

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Search the Archive</h1>

      <form onSubmit={handleSearch} className="mb-6" role="search" aria-label="Search public documents">
        <div className="flex gap-2">
          <label htmlFor="public-search" className="sr-only">Search query</label>
          <input id="public-search" type="search" value={localQuery} onChange={(e) => setLocalQuery(e.target.value)}
            placeholder="Search by title, content, subject..."
            className="min-h-[44px] flex-1 rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
          <button type="submit"
            className="min-h-[44px] px-6 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
            Search
          </button>
        </div>
      </form>

      <div className="mb-6 flex flex-wrap items-end gap-4" role="group" aria-label="Search filters">
        <div>
          <label htmlFor="pub-date-from" className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Date from</label>
          <input id="pub-date-from" type="date" value={dateFrom}
            onChange={(e) => { const p = new URLSearchParams(searchParams); if (e.target.value) { p.set('date_from', e.target.value); } else { p.delete('date_from'); } p.set('page', '1'); setSearchParams(p); }}
            className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
        </div>
        <div>
          <label htmlFor="pub-date-to" className="block text-xs font-medium text-gray-600 dark:text-gray-400 mb-1">Date to</label>
          <input id="pub-date-to" type="date" value={dateTo}
            onChange={(e) => { const p = new URLSearchParams(searchParams); if (e.target.value) { p.set('date_to', e.target.value); } else { p.delete('date_to'); } p.set('page', '1'); setSearchParams(p); }}
            className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
        </div>
      </div>

      {!hasQuery && <p className="text-gray-500 dark:text-gray-400 text-center py-16">Enter a search term to find documents in the archive.</p>}

      {isLoading && <div className="flex justify-center py-16"><Spinner label="Searching" /></div>}
      {isError && <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Search failed. Please try again.</div>}

      {data && data.items.length === 0 && hasQuery && <p className="text-gray-500 dark:text-gray-400 text-center py-16">No documents match your search.</p>}

      {data && data.items.length > 0 && (
        <>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">{data.total} result{data.total !== 1 ? 's' : ''}</p>
          <ul className="space-y-4">
            {data.items.map((doc) => (
              <li key={doc.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
                <Link to={`/public/documents/${doc.id}`}
                  className="text-blue-700 dark:text-blue-400 hover:underline font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                  {doc.title}
                </Link>
                <div className="mt-1 flex items-center gap-3 text-xs text-gray-500 dark:text-gray-400">
                  {doc.date_display && <span>{doc.date_display}</span>}
                  {doc.creator && <span>by {doc.creator.authorized_name}</span>}
                </div>
                {doc.scope_and_content && <p className="mt-2 text-sm text-gray-600 dark:text-gray-400 line-clamp-2">{doc.scope_and_content}</p>}
              </li>
            ))}
          </ul>

          {data.pages > 1 && (
            <nav aria-label="Search results pagination" className="mt-6 flex items-center justify-center gap-2">
              <button type="button" disabled={page <= 1}
                onClick={() => { const p = new URLSearchParams(searchParams); p.set('page', String(page - 1)); setSearchParams(p); }}
                className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Previous page">Previous</button>
              <span className="text-sm text-gray-600 dark:text-gray-400" aria-current="page">Page {data.page} of {data.pages}</span>
              <button type="button" disabled={page >= data.pages}
                onClick={() => { const p = new URLSearchParams(searchParams); p.set('page', String(page + 1)); setSearchParams(p); }}
                className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Next page">Next</button>
            </nav>
          )}
        </>
      )}
    </div>
  );
}
