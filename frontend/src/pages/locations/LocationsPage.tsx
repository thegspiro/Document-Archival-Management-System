/**
 * Location list with search and filtering by location type.
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { locationsApi } from '../../api/locations';
import type { Location, PaginatedResponse } from '../../types/api';

export default function LocationsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('q') ?? '');
  const page = Number(searchParams.get('page') ?? '1');

  const locQuery = useQuery<PaginatedResponse<Location>>({
    queryKey: ['locations', search, page],
    queryFn: () => locationsApi.list({ ...(search ? { q: search } : {}), page, per_page: 25 }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams({ q: search, page: '1' });
  };

  const items = locQuery.data?.items ?? [];

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Locations</h1>
        <Link to="/locations/new" className="min-h-[44px] inline-flex items-center px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          Add Location
        </Link>
      </div>

      <form onSubmit={handleSearch} className="mb-4 flex gap-4">
        <div className="flex-1 max-w-md">
          <label htmlFor="location-search" className="sr-only">Search locations</label>
          <input id="location-search" type="search" placeholder="Search locations..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Search locations" />
        </div>
        <button type="submit" className="min-h-[44px] px-4 py-2 rounded bg-blue-700 text-white text-sm hover:bg-blue-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]">Search</button>
      </form>

      {locQuery.isLoading && (
        <div role="status" aria-label="Loading locations" className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent" aria-hidden="true" />
          <p className="mt-2 text-gray-500 dark:text-gray-400">Loading locations...</p>
        </div>
      )}

      {locQuery.isError && (
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load locations.</div>
      )}

      {locQuery.data && items.length === 0 && <p className="text-center py-8 text-gray-500 dark:text-gray-400">No locations found.</p>}

      {items.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Name</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Coordinates</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Address</th>
                <th scope="col" className="px-4 py-3"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900">
              {items.map((loc) => (
                <tr key={loc.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-4 py-3">
                    <Link to={`/locations/${loc.id}`} className="text-blue-700 dark:text-blue-400 hover:underline font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">{loc.authorized_name}</Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">
                    {loc.geo_latitude != null && loc.geo_longitude != null ? `${loc.geo_latitude}, ${loc.geo_longitude}` : '\u2014'}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{loc.address ?? '\u2014'}</td>
                  <td className="px-4 py-3 text-right">
                    <Link to={`/locations/${loc.id}`} className="text-xs text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {locQuery.data && locQuery.data.pages > 1 && (
        <nav aria-label="Locations pagination" className="mt-4 flex items-center justify-center gap-2">
          <button type="button" disabled={page <= 1} onClick={() => setSearchParams({ q: search, page: String(page - 1) })} className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Previous page">Previous</button>
          <span className="text-sm text-gray-600 dark:text-gray-400" aria-current="page">Page {locQuery.data.page} of {locQuery.data.pages}</span>
          <button type="button" disabled={page >= locQuery.data.pages} onClick={() => setSearchParams({ q: search, page: String(page + 1) })} className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Next page">Next</button>
        </nav>
      )}
    </div>
  );
}
