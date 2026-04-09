/**
 * Event detail page. Shows event info, linked documents, people, and locations.
 */
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { eventsApi } from '../../api/events';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import type { Event } from '../../types/api';

export default function EventDetailPage() {
  const { id } = useParams<{ id: string }>();
  const eventId = Number(id);

  const { data: event, isLoading, isError } = useQuery<Event>({
    queryKey: ['events', eventId],
    queryFn: () => eventsApi.get(eventId),
    enabled: !Number.isNaN(eventId),
  });

  const docsQuery = useQuery({
    queryKey: ['events', eventId, 'documents'],
    queryFn: () => apiClient.get(`/events/${eventId}/documents`).then((r) => r.data),
    enabled: !Number.isNaN(eventId),
  });

  const authQuery = useQuery({
    queryKey: ['events', eventId, 'authorities'],
    queryFn: () => apiClient.get(`/events/${eventId}/authorities`).then((r) => r.data),
    enabled: !Number.isNaN(eventId),
  });

  const locsQuery = useQuery({
    queryKey: ['events', eventId, 'locations'],
    queryFn: () => apiClient.get(`/events/${eventId}/locations`).then((r) => r.data),
    enabled: !Number.isNaN(eventId),
  });

  if (isLoading) return <div className="flex items-center justify-center py-16"><Spinner label="Loading event" /></div>;

  if (isError || !event) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load event.</div>
        <Link to="/events" className="mt-4 inline-block text-blue-700 dark:text-blue-400 hover:underline">Back to events</Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <nav aria-label="Breadcrumb" className="text-sm text-gray-500 dark:text-gray-400 mb-2">
        <Link to="/events" className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">Events</Link>
        <span aria-hidden="true"> / </span>
        <span aria-current="page">{event.title}</span>
      </nav>

      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">{event.title}</h1>
      <div className="mb-6 flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
        {event.date_display && <span>{event.date_display}</span>}
        {event.is_public && <span className="text-xs text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/30 rounded px-2 py-0.5">Public</span>}
      </div>

      {event.description && (
        <section aria-labelledby="evt-desc" className="mb-6">
          <h2 id="evt-desc" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Description</h2>
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{event.description}</div>
        </section>
      )}

      <section aria-labelledby="evt-docs" className="mb-6">
        <h2 id="evt-docs" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Documents</h2>
        {docsQuery.isLoading && <Spinner size="sm" label="Loading documents" />}
        {docsQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load documents.</p>}
        {docsQuery.data && Array.isArray(docsQuery.data) && docsQuery.data.length === 0 && <p className="text-gray-500 dark:text-gray-400 text-sm">No documents linked.</p>}
        {docsQuery.data && Array.isArray(docsQuery.data) && docsQuery.data.length > 0 && (
          <ul className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
            {(docsQuery.data as Array<{ id: number; document?: { id: number; title: string } }>).map((link) => (
              <li key={link.id} className="px-4 py-3">
                <Link to={`/archive/documents/${link.document?.id ?? link.id}`}
                  className="text-blue-700 dark:text-blue-400 hover:underline font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                  {link.document?.title ?? `Document #${link.id}`}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="evt-people" className="mb-6">
        <h2 id="evt-people" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">People &amp; Organizations</h2>
        {authQuery.isLoading && <Spinner size="sm" label="Loading people" />}
        {authQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load people.</p>}
        {authQuery.data && Array.isArray(authQuery.data) && authQuery.data.length === 0 && <p className="text-gray-500 dark:text-gray-400 text-sm">No people linked.</p>}
        {authQuery.data && Array.isArray(authQuery.data) && authQuery.data.length > 0 && (
          <ul className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
            {(authQuery.data as Array<{ id: number; authority?: { id: number; authorized_name: string } }>).map((link) => (
              <li key={link.id} className="px-4 py-3">
                <Link to={`/people/${link.authority?.id ?? link.id}`}
                  className="text-blue-700 dark:text-blue-400 hover:underline font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                  {link.authority?.authorized_name ?? `Authority #${link.id}`}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="evt-locs">
        <h2 id="evt-locs" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Locations</h2>
        {locsQuery.isLoading && <Spinner size="sm" label="Loading locations" />}
        {locsQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load locations.</p>}
        {locsQuery.data && Array.isArray(locsQuery.data) && locsQuery.data.length === 0 && <p className="text-gray-500 dark:text-gray-400 text-sm">No locations linked.</p>}
        {locsQuery.data && Array.isArray(locsQuery.data) && locsQuery.data.length > 0 && (
          <ul className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
            {(locsQuery.data as Array<{ id: number; location?: { id: number; authorized_name: string } }>).map((link) => (
              <li key={link.id} className="px-4 py-3">
                <Link to={`/locations/${link.location?.id ?? link.id}`}
                  className="text-blue-700 dark:text-blue-400 hover:underline font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                  {link.location?.authorized_name ?? `Location #${link.id}`}
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
