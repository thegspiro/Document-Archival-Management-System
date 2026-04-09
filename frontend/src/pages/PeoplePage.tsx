/**
 * Authority records list page. Displays persons, organizations, and families
 * with search and entity type filtering.
 */
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { authorityApi } from '../api/authority';
import Spinner from '../components/ui/Spinner';
import type { AuthorityRecord, PaginatedResponse } from '../types/api';

const ENTITY_TYPES = [
  { value: '', label: 'All types' },
  { value: 'person', label: 'Persons' },
  { value: 'organization', label: 'Organizations' },
  { value: 'family', label: 'Families' },
];

function EntityTypeBadge({ type }: { type: string }) {
  const styles: Record<string, string> = {
    person: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
    organization: 'bg-purple-100 dark:bg-purple-900/40 text-purple-700 dark:text-purple-300',
    family: 'bg-amber-100 dark:bg-amber-900/40 text-amber-700 dark:text-amber-300',
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium capitalize ${styles[type] ?? styles.person}`}>{type}</span>
  );
}

export default function PeoplePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get('page') ?? '1');
  const entityType = searchParams.get('type') ?? '';
  const searchQuery = searchParams.get('q') ?? '';

  const { data, isLoading, isError } = useQuery<PaginatedResponse<AuthorityRecord>>({
    queryKey: ['authority', page, entityType, searchQuery],
    queryFn: () => authorityApi.list({
      page, per_page: 25,
      ...(entityType ? { entity_type: entityType } : {}),
      ...(searchQuery ? { q: searchQuery } : {}),
    }),
  });

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const q = (formData.get('q') as string)?.trim() ?? '';
    const next = new URLSearchParams(searchParams);
    if (q) { next.set('q', q); } else { next.delete('q'); }
    next.set('page', '1');
    setSearchParams(next);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">People &amp; Organizations</h1>
      </div>

      <div className="mb-6 flex flex-wrap items-end gap-4">
        <form onSubmit={handleSearch} className="flex gap-2" role="search" aria-label="Search authority records">
          <label htmlFor="authority-search" className="sr-only">Search by name</label>
          <input id="authority-search" name="q" type="search" defaultValue={searchQuery} placeholder="Search by name..."
            className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
          <button type="submit"
            className="min-h-[44px] px-4 py-2 rounded bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]">
            Search
          </button>
        </form>
        <div>
          <label htmlFor="entity-type-filter" className="sr-only">Filter by entity type</label>
          <select id="entity-type-filter" value={entityType}
            onChange={(e) => { const next = new URLSearchParams(searchParams); if (e.target.value) { next.set('type', e.target.value); } else { next.delete('type'); } next.set('page', '1'); setSearchParams(next); }}
            className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]">
            {ENTITY_TYPES.map((opt) => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
          </select>
        </div>
      </div>

      {isLoading && <div className="flex items-center justify-center py-16"><Spinner label="Loading authority records" /></div>}
      {isError && (
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load authority records.</div>
      )}

      {data && data.items.length === 0 && <p className="text-gray-500 dark:text-gray-400 text-center py-16">No authority records found.</p>}

      {data && data.items.length > 0 && (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Name</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Type</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Dates</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Public</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {data.items.map((record) => (
                  <tr key={record.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      <Link to={`/people/${record.id}`}
                        className="text-blue-700 dark:text-blue-400 hover:underline font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                        {record.authorized_name}
                      </Link>
                      {record.created_by_ner && <span className="ml-2 text-xs text-amber-600 dark:text-amber-400">(NER)</span>}
                    </td>
                    <td className="px-4 py-3"><EntityTypeBadge type={record.entity_type} /></td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{record.dates ?? '\u2014'}</td>
                    <td className="px-4 py-3">{record.is_public ? <span className="text-xs text-green-700 dark:text-green-400">Yes</span> : <span className="text-xs text-gray-400">No</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.pages > 1 && (
            <nav aria-label="Authority records pagination" className="mt-4 flex items-center justify-center gap-2">
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
