/**
 * Location detail page. Shows location info, linked documents, and events.
 */
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { locationsApi } from '../../api/locations';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import type { Location } from '../../types/api';

export default function LocationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const locationId = Number(id);

  const { data: location, isLoading, isError } = useQuery<Location>({
    queryKey: ['locations', locationId],
    queryFn: () => locationsApi.get(locationId),
    enabled: !Number.isNaN(locationId),
  });

  const docsQuery = useQuery({
    queryKey: ['locations', locationId, 'documents'],
    queryFn: () => apiClient.get(`/locations/${locationId}/documents`).then((r) => r.data),
    enabled: !Number.isNaN(locationId),
  });

  const eventsQuery = useQuery({
    queryKey: ['locations', locationId, 'events'],
    queryFn: () => apiClient.get(`/locations/${locationId}/events`).then((r) => r.data),
    enabled: !Number.isNaN(locationId),
  });

  if (isLoading) return <div className="flex items-center justify-center py-16"><Spinner label="Loading location" /></div>;

  if (isError || !location) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load location.</div>
        <Link to="/locations" className="mt-4 inline-block text-blue-700 dark:text-blue-400 hover:underline">Back to locations</Link>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <nav aria-label="Breadcrumb" className="text-sm text-gray-500 dark:text-gray-400 mb-2">
        <Link to="/locations" className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">Locations</Link>
        <span aria-hidden="true"> / </span>
        <span aria-current="page">{location.authorized_name}</span>
      </nav>

      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">{location.authorized_name}</h1>
      <div className="mb-6 flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
        {location.address && <span>{location.address}</span>}
        {location.geo_latitude != null && location.geo_longitude != null && (
          <span>({location.geo_latitude.toFixed(4)}, {location.geo_longitude.toFixed(4)})</span>
        )}
        {location.is_public && <span className="text-xs text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/30 rounded px-2 py-0.5">Public</span>}
      </div>

      {location.description && (
        <section aria-labelledby="desc-heading" className="mb-6">
          <h2 id="desc-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Description</h2>
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{location.description}</div>
        </section>
      )}

      {location.variant_names && (
        <section aria-labelledby="variants-heading" className="mb-6">
          <h2 id="variants-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Variant Names</h2>
          <ul className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-1">
            {location.variant_names.split('|').map((name, i) => <li key={i} className="text-sm text-gray-700 dark:text-gray-300">{name.trim()}</li>)}
          </ul>
        </section>
      )}

      <section aria-labelledby="loc-docs-heading" className="mb-6">
        <h2 id="loc-docs-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Linked Documents</h2>
        {docsQuery.isLoading && <Spinner size="sm" label="Loading documents" />}
        {docsQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load documents.</p>}
        {docsQuery.data && Array.isArray(docsQuery.data) && docsQuery.data.length === 0 && <p className="text-gray-500 dark:text-gray-400 text-sm">No documents linked.</p>}
        {docsQuery.data && Array.isArray(docsQuery.data) && docsQuery.data.length > 0 && (
          <ul className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
            {(docsQuery.data as Array<{ id: number; title: string; date_display?: string }>).map((doc) => (
              <li key={doc.id} className="px-4 py-3">
                <Link to={`/archive/documents/${doc.id}`} className="text-blue-700 dark:text-blue-400 hover:underline font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">{doc.title}</Link>
                {doc.date_display && <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">{doc.date_display}</span>}
              </li>
            ))}
          </ul>
        )}
      </section>

      <section aria-labelledby="loc-events-heading">
        <h2 id="loc-events-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Linked Events</h2>
        {eventsQuery.isLoading && <Spinner size="sm" label="Loading events" />}
        {eventsQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load events.</p>}
        {eventsQuery.data && Array.isArray(eventsQuery.data) && eventsQuery.data.length === 0 && <p className="text-gray-500 dark:text-gray-400 text-sm">No events linked.</p>}
        {eventsQuery.data && Array.isArray(eventsQuery.data) && eventsQuery.data.length > 0 && (
          <ul className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
            {(eventsQuery.data as Array<{ id: number; title: string; date_display?: string }>).map((evt) => (
              <li key={evt.id} className="px-4 py-3">
                <Link to={`/events/${evt.id}`} className="text-blue-700 dark:text-blue-400 hover:underline font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">{evt.title}</Link>
                {evt.date_display && <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">{evt.date_display}</span>}
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  );
}
