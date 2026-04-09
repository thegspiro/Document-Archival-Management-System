/**
 * Authority records list with search and filter by entity_type.
 * Uses React Query for data fetching from the authority API.
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { authorityApi } from '../api/authority';
import type { AuthorityRecord, PaginatedResponse } from '../types/api';

export default function PeoplePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('q') ?? '');
  const entityType = searchParams.get('entity_type') ?? '';
  const page = Number(searchParams.get('page') ?? '1');

  const authQuery = useQuery<PaginatedResponse<AuthorityRecord>>({
    queryKey: ['authority', search, entityType, page],
    queryFn: () =>
      authorityApi.list({
        ...(search ? { q: search } : {}),
        ...(entityType ? { entity_type: entityType } : {}),
        page,
        per_page: 25,
      }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams((prev) => {
      prev.set('q', search);
      prev.set('page', '1');
      return prev;
    });
  };

  const items = authQuery.data?.items ?? [];

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Authority Records</h1>
        <Link
          to="/people/new"
          className="min-h-[44px] inline-flex items-center px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2"
        >
          Add Authority Record
        </Link>
      </div>

      <form onSubmit={handleSearch} className="mb-4 flex gap-4">
        <div className="flex-1 max-w-md">
          <label htmlFor="people-search" className="sr-only">Search authority records</label>
          <input
            id="people-search"
            type="search"
            placeholder="Search by name..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
            aria-label="Search authority records"
          />
        </div>
        <select
          value={entityType}
          onChange={(e) => {
            setSearchParams((prev) => {
              prev.set('entity_type', e.target.value);
              prev.set('page', '1');
              return prev;
            });
          }}
          aria-label="Filter by entity type"
          className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
        >
          <option value="">All types</option>
          <option value="person">Person</option>
          <option value="organization">Organization</option>
          <option value="family">Family</option>
        </select>
        <button type="submit" className="min-h-[44px] px-4 py-2 rounded bg-blue-700 text-white text-sm hover:bg-blue-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]">
          Search
        </button>
      </form>

      {authQuery.isLoading && (
        <div role="status" aria-label="Loading authority records" className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent" aria-hidden="true" />
          <p className="mt-2 text-gray-500 dark:text-gray-400">Loading authority records...</p>
        </div>
      )}

      {authQuery.isError && (
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
          Failed to load authority records.
        </div>
      )}

      {authQuery.data && items.length === 0 && (
        <p className="text-center py-8 text-gray-500 dark:text-gray-400">No authority records found.</p>
      )}

      {items.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Name</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Type</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Dates</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Wikidata</th>
                <th scope="col" className="px-4 py-3"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900">
              {items.map((record) => (
                <tr key={record.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-4 py-3">
                    <Link to={`/people/${record.id}`} className="text-blue-700 dark:text-blue-400 hover:underline font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                      {record.authorized_name}
                    </Link>
                    {record.created_by_ner && (
                      <span className="ml-2 text-xs bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200 px-1.5 py-0.5 rounded">NER</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400 capitalize">{record.entity_type}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{record.dates ?? '\u2014'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{record.wikidata_qid ?? '\u2014'}</td>
                  <td className="px-4 py-3 text-right">
                    <Link to={`/people/${record.id}`} className="min-h-[44px] inline-flex items-center px-3 py-1 text-xs text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {authQuery.data && authQuery.data.pages > 1 && (
        <nav aria-label="Authority records pagination" className="mt-4 flex items-center justify-center gap-2">
          <button type="button" disabled={page <= 1} onClick={() => setSearchParams((prev) => { prev.set('page', String(page - 1)); return prev; })} className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Previous page">
            Previous
          </button>
          <span className="text-sm text-gray-600 dark:text-gray-400" aria-current="page">Page {authQuery.data.page} of {authQuery.data.pages}</span>
          <button type="button" disabled={page >= authQuery.data.pages} onClick={() => setSearchParams((prev) => { prev.set('page', String(page + 1)); return prev; })} className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Next page">
            Next
          </button>
        </nav>
      )}
    </div>
  );
}
