/**
 * Location detail page with map placeholder, linked documents, and linked events.
 */
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { locationsApi } from '../../api/locations';
import apiClient from '../../api/client';
import type { Location } from '../../types/api';

export default function LocationDetailPage() {
  const { id } = useParams<{ id: string }>();
  const locationId = Number(id);

  const locQuery = useQuery<Location>({
    queryKey: ['location', locationId],
    queryFn: () => locationsApi.get(locationId),
    enabled: !isNaN(locationId),
  });

  const docsQuery = useQuery({
    queryKey: ['location-docs', locationId],
    queryFn: () => apiClient.get(`/locations/${locationId}/documents`).then((r) => r.data),
    enabled: !isNaN(locationId),
  });

  const eventsQuery = useQuery({
    queryKey: ['location-events', locationId],
    queryFn: () => apiClient.get(`/locations/${locationId}/events`).then((r) => r.data),
    enabled: !isNaN(locationId),
  });

  const loc = locQuery.data;

  if (locQuery.isLoading) {
    return (
      <div role="status" aria-label="Loading location" className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent" aria-hidden="true" />
        <span className="ml-3 text-gray-500 dark:text-gray-400">Loading location...</span>
      </div>
    );
  }

  if (locQuery.isError || !loc) {
    return (
      <div role="alert" className="p-6 max-w-3xl mx-auto">
        <div className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Location not found.</div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6">
      <nav className="mb-4" aria-label="Breadcrumb">
        <Link to="/locations" className="text-sm text-blue-600 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">&larr; Back to Locations</Link>
      </nav>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{loc.authorized_name}</h1>
          {loc.variant_names && <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">Also known as: {loc.variant_names.replace(/\|/g, ', ')}</p>}
          {loc.address && <p className="text-sm text-gray-500 dark:text-gray-400">{loc.address}</p>}
        </div>
        <Link to={`/locations/${loc.id}/edit`} className="min-h-[44px] inline-flex items-center px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">Edit</Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <section className="lg:col-span-2 space-y-6">
          {/* Map */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Map</h2>
            {loc.geo_latitude != null && loc.geo_longitude != null ? (
              <div role="application" aria-label={`Map showing ${loc.authorized_name}`} className="h-64 bg-gray-100 dark:bg-gray-800 rounded flex items-center justify-center text-sm text-gray-500 dark:text-gray-400">
                Map: {loc.geo_latitude}, {loc.geo_longitude}
                <p className="sr-only">Coordinates: latitude {loc.geo_latitude}, longitude {loc.geo_longitude}</p>
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">No coordinates available.</p>
            )}
          </div>

          {/* Documents */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Linked Documents</h2>
            {docsQuery.isLoading && <p className="text-sm text-gray-500">Loading...</p>}
            {docsQuery.data && Array.isArray(docsQuery.data) && docsQuery.data.length > 0 ? (
              <ul className="divide-y divide-gray-100 dark:divide-gray-700">
                {(docsQuery.data as Array<{ id: number; document: { id: number; title: string }; link_type: string }>).map((link) => (
                  <li key={link.id} className="py-2 text-sm">
                    <Link to={`/archive/documents/${link.document.id}`} className="text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">{link.document.title}</Link>
                    <span className="text-gray-400 dark:text-gray-500 ml-1 text-xs">({link.link_type})</span>
                  </li>
                ))}
              </ul>
            ) : (!docsQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">No linked documents.</p>)}
          </div>

          {/* Events */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Events at this Location</h2>
            {eventsQuery.isLoading && <p className="text-sm text-gray-500">Loading...</p>}
            {eventsQuery.data && Array.isArray(eventsQuery.data) && eventsQuery.data.length > 0 ? (
              <ul className="divide-y divide-gray-100 dark:divide-gray-700">
                {(eventsQuery.data as Array<{ id: number; event: { id: number; title: string; date_display?: string } }>).map((link) => (
                  <li key={link.id} className="py-2 text-sm">
                    <Link to={`/events/${link.event.id}`} className="text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">{link.event.title}</Link>
                    {link.event.date_display && <span className="text-gray-400 dark:text-gray-500 ml-1 text-xs">{link.event.date_display}</span>}
                  </li>
                ))}
              </ul>
            ) : (!eventsQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">No events at this location.</p>)}
          </div>
        </section>

        <aside>
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Details</h2>
            <dl className="space-y-2 text-sm">
              {loc.description && (<><dt className="font-medium text-gray-700 dark:text-gray-300">Description</dt><dd className="text-gray-600 dark:text-gray-400">{loc.description}</dd></>)}
              <dt className="font-medium text-gray-700 dark:text-gray-300">Coordinates</dt>
              <dd className="text-gray-600 dark:text-gray-400">{loc.geo_latitude != null ? `${loc.geo_latitude}, ${loc.geo_longitude}` : 'Not set'}</dd>
              <dt className="font-medium text-gray-700 dark:text-gray-300">Public</dt>
              <dd className="text-gray-600 dark:text-gray-400">{loc.is_public ? 'Yes' : 'No'}</dd>
            </dl>
          </div>
        </aside>
      </div>
    </div>
  );
}
