/**
 * Event detail with linked documents, people, locations, and timeline.
 * Fetches data using React Query from the events API.
 */
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { eventsApi } from '../../api/events';
import apiClient from '../../api/client';
import type { Event } from '../../types/api';

export default function EventDetailPage() {
  const { id } = useParams<{ id: string }>();
  const eventId = Number(id);

  const eventQuery = useQuery<Event>({
    queryKey: ['event', eventId],
    queryFn: () => eventsApi.get(eventId),
    enabled: !isNaN(eventId),
  });

  const docsQuery = useQuery({
    queryKey: ['event-docs', eventId],
    queryFn: () => apiClient.get(`/events/${eventId}/documents`).then((r) => r.data),
    enabled: !isNaN(eventId),
  });

  const authQuery = useQuery({
    queryKey: ['event-authorities', eventId],
    queryFn: () => apiClient.get(`/events/${eventId}/authorities`).then((r) => r.data),
    enabled: !isNaN(eventId),
  });

  const locQuery = useQuery({
    queryKey: ['event-locations', eventId],
    queryFn: () => apiClient.get(`/events/${eventId}/locations`).then((r) => r.data),
    enabled: !isNaN(eventId),
  });

  const evt = eventQuery.data;

  if (eventQuery.isLoading) {
    return (
      <div role="status" aria-label="Loading event" className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent" aria-hidden="true" />
        <span className="ml-3 text-gray-500 dark:text-gray-400">Loading event...</span>
      </div>
    );
  }

  if (eventQuery.isError || !evt) {
    return (
      <div role="alert" className="p-6 max-w-3xl mx-auto">
        <div className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Event not found.</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <nav className="mb-4 text-sm text-gray-500 dark:text-gray-400" aria-label="Breadcrumb">
        <Link to="/events" className="hover:text-blue-600 dark:hover:text-blue-400 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">Events</Link>
        <span className="mx-2" aria-hidden="true">/</span>
        <span className="text-gray-900 dark:text-gray-100" aria-current="page">{evt.title}</span>
      </nav>

      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{evt.title}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            {evt.date_display && <span>{evt.date_display}</span>}
            {evt.is_public && <span className="ml-3 text-xs bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200 px-2 py-0.5 rounded">Public</span>}
          </p>
        </div>
        <Link to={`/events/${evt.id}/edit`} className="min-h-[44px] inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          Edit Event
        </Link>
      </div>

      {evt.description && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 mb-6">
          <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{evt.description}</p>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Documents */}
          <section className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Linked Documents</h2>
            {docsQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">Loading...</p>}
            {docsQuery.data && Array.isArray(docsQuery.data) && docsQuery.data.length > 0 ? (
              <ul className="divide-y divide-gray-100 dark:divide-gray-700">
                {(docsQuery.data as Array<{ id: number; document: { id: number; title: string; accession_number?: string }; link_type: string }>).map((link) => (
                  <li key={link.id} className="py-2 text-sm">
                    <Link to={`/archive/documents/${link.document.id}`} className="text-blue-700 dark:text-blue-400 hover:underline font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">{link.document.title}</Link>
                    <span className="text-gray-400 dark:text-gray-500 ml-2 text-xs">({link.link_type})</span>
                    {link.document.accession_number && <span className="text-gray-400 dark:text-gray-500 ml-2 text-xs">{link.document.accession_number}</span>}
                  </li>
                ))}
              </ul>
            ) : (!docsQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">No documents linked to this event.</p>)}
          </section>
        </div>

        <div className="space-y-6">
          {/* People */}
          <section className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">People</h2>
            {authQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">Loading...</p>}
            {authQuery.data && Array.isArray(authQuery.data) && authQuery.data.length > 0 ? (
              <ul className="space-y-1">
                {(authQuery.data as Array<{ id: number; authority: { id: number; authorized_name: string }; role: { term: string } }>).map((link) => (
                  <li key={link.id} className="text-sm">
                    <Link to={`/people/${link.authority.id}`} className="text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">{link.authority.authorized_name}</Link>
                    <span className="text-gray-400 dark:text-gray-500 ml-1 text-xs">({link.role.term})</span>
                  </li>
                ))}
              </ul>
            ) : (!authQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">No people linked.</p>)}
          </section>

          {/* Locations */}
          <section className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Locations</h2>
            {locQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">Loading...</p>}
            {locQuery.data && Array.isArray(locQuery.data) && locQuery.data.length > 0 ? (
              <ul className="space-y-1">
                {(locQuery.data as Array<{ id: number; location: { id: number; authorized_name: string }; link_type: string }>).map((link) => (
                  <li key={link.id} className="text-sm">
                    <Link to={`/locations/${link.location.id}`} className="text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">{link.location.authorized_name}</Link>
                    <span className="text-gray-400 dark:text-gray-500 ml-1 text-xs">({link.link_type})</span>
                  </li>
                ))}
              </ul>
            ) : (!locQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">No locations linked.</p>)}
          </section>
        </div>
      </div>
    </div>
  );
}
