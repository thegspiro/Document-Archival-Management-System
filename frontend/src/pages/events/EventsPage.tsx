/**
 * Events list with search and filter by event_type.
 * Fetches events from the events API using React Query.
 */
import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { eventsApi } from '../../api/events';
import type { Event, PaginatedResponse } from '../../types/api';

export default function EventsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [search, setSearch] = useState(searchParams.get('q') ?? '');
  const page = Number(searchParams.get('page') ?? '1');

  const eventsQuery = useQuery<PaginatedResponse<Event>>({
    queryKey: ['events', search, page],
    queryFn: () => eventsApi.list({ ...(search ? { q: search } : {}), page, per_page: 25 }),
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    setSearchParams({ q: search, page: '1' });
  };

  const items = eventsQuery.data?.items ?? [];

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Events</h1>
        <Link to="/events/new" className="min-h-[44px] inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          New Event
        </Link>
      </div>

      <form onSubmit={handleSearch} className="mb-4 flex gap-4">
        <div className="flex-1 max-w-md">
          <label htmlFor="event-search" className="sr-only">Search events</label>
          <input id="event-search" type="search" placeholder="Search events..." value={search} onChange={(e) => setSearch(e.target.value)} className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Search events" />
        </div>
        <button type="submit" className="min-h-[44px] px-4 py-2 rounded bg-blue-700 text-white text-sm hover:bg-blue-800 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]">Search</button>
      </form>

      {eventsQuery.isLoading && (
        <div role="status" aria-label="Loading events" className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent" aria-hidden="true" />
          <p className="mt-2 text-gray-500 dark:text-gray-400">Loading events...</p>
        </div>
      )}

      {eventsQuery.isError && (
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load events.</div>
      )}

      {eventsQuery.data && items.length === 0 && (
        <p className="text-center py-8 text-gray-500 dark:text-gray-400">No events found. Create your first event to get started.</p>
      )}

      {items.length > 0 && (
        <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
          <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
            <thead className="bg-gray-50 dark:bg-gray-800">
              <tr>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Title</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Date</th>
                <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Public</th>
                <th scope="col" className="px-4 py-3"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900">
              {items.map((event) => (
                <tr key={event.id} className="hover:bg-gray-50 dark:hover:bg-gray-800">
                  <td className="px-4 py-3">
                    <Link to={`/events/${event.id}`} className="text-blue-700 dark:text-blue-400 hover:underline font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">{event.title}</Link>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{event.date_display ?? '\u2014'}</td>
                  <td className="px-4 py-3 text-sm text-gray-600 dark:text-gray-400">{event.is_public ? 'Yes' : 'No'}</td>
                  <td className="px-4 py-3 text-right">
                    <Link to={`/events/${event.id}`} className="text-xs text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">View</Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {eventsQuery.data && eventsQuery.data.pages > 1 && (
        <nav aria-label="Events pagination" className="mt-4 flex items-center justify-center gap-2">
          <button type="button" disabled={page <= 1} onClick={() => setSearchParams({ q: search, page: String(page - 1) })} className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Previous page">Previous</button>
          <span className="text-sm text-gray-600 dark:text-gray-400" aria-current="page">Page {eventsQuery.data.page} of {eventsQuery.data.pages}</span>
          <button type="button" disabled={page >= eventsQuery.data.pages} onClick={() => setSearchParams({ q: search, page: String(page + 1) })} className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]" aria-label="Next page">Next</button>
        </nav>
      )}
    </div>
  );
}
