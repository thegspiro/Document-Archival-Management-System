/**
 * Events list page. Browse historical events with search.
 */
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { eventsApi } from '../../api/events';
import Spinner from '../../components/ui/Spinner';
import type { Event, PaginatedResponse } from '../../types/api';

export default function EventsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get('page') ?? '1');
  const q = searchParams.get('q') ?? '';

  const { data, isLoading, isError } = useQuery<PaginatedResponse<Event>>({
    queryKey: ['events', page, q],
    queryFn: () => eventsApi.list({ page, per_page: 25, ...(q ? { q } : {}) }),
  });

  const handleSearch = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const query = (fd.get('q') as string)?.trim() ?? '';
    const next = new URLSearchParams(searchParams);
    if (query) { next.set('q', query); } else { next.delete('q'); }
    next.set('page', '1');
    setSearchParams(next);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Events</h1>
        <Link to="/events/new"
          className="min-h-[44px] inline-flex items-center px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          New Event
        </Link>
      </div>

      <form onSubmit={handleSearch} className="mb-6 flex gap-2" role="search" aria-label="Search events">
        <label htmlFor="event-search" className="sr-only">Search events</label>
        <input id="event-search" name="q" type="search" defaultValue={q} placeholder="Search by title..."
          className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
        <button type="submit"
          className="min-h-[44px] px-4 py-2 rounded bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 text-sm font-medium hover:bg-gray-300 dark:hover:bg-gray-600 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]">
          Search
        </button>
      </form>

      {isLoading && <div className="flex items-center justify-center py-16"><Spinner label="Loading events" /></div>}
      {isError && <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load events.</div>}
      {data && data.items.length === 0 && <p className="text-gray-500 dark:text-gray-400 text-center py-16">No events found.</p>}

      {data && data.items.length > 0 && (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Title</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Date</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Public</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {data.items.map((evt) => (
                  <tr key={evt.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      <Link to={`/events/${evt.id}`}
                        className="text-blue-700 dark:text-blue-400 hover:underline font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                        {evt.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{evt.date_display ?? evt.date_start ?? '\u2014'}</td>
                    <td className="px-4 py-3">{evt.is_public ? <span className="text-xs text-green-700 dark:text-green-400">Yes</span> : <span className="text-xs text-gray-400">No</span>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {data.pages > 1 && (
            <nav aria-label="Events pagination" className="mt-4 flex items-center justify-center gap-2">
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
