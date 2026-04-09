/**
 * Authority record detail page. Shows biographical/organizational info,
 * linked documents, events, and optional Wikidata enrichment.
 */
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { authorityApi } from '../api/authority';
import apiClient from '../api/client';
import Spinner from '../components/ui/Spinner';
import type { AuthorityRecord, Document } from '../types/api';

export default function PersonDetailPage() {
  const { id } = useParams<{ id: string }>();
  const recordId = Number(id);

  const { data: record, isLoading, isError } = useQuery<AuthorityRecord>({
    queryKey: ['authority', recordId],
    queryFn: () => authorityApi.get(recordId),
    enabled: !Number.isNaN(recordId),
  });

  const documentsQuery = useQuery<Document[]>({
    queryKey: ['authority', recordId, 'documents'],
    queryFn: () => authorityApi.getDocuments(recordId),
    enabled: !Number.isNaN(recordId),
  });

  const eventsQuery = useQuery({
    queryKey: ['authority', recordId, 'events'],
    queryFn: () => apiClient.get(`/authority/${recordId}/events`).then((r) => r.data),
    enabled: !Number.isNaN(recordId),
  });

  if (isLoading) return <div className="flex items-center justify-center py-16"><Spinner label="Loading authority record" /></div>;

  if (isError || !record) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load authority record.</div>
        <Link to="/people" className="mt-4 inline-block text-blue-700 dark:text-blue-400 hover:underline">Back to records</Link>
      </div>
    );
  }

  const typeLabels: Record<string, string> = { person: 'Person', organization: 'Organization', family: 'Family' };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <nav aria-label="Breadcrumb" className="text-sm text-gray-500 dark:text-gray-400 mb-2">
        <Link to="/people" className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">People &amp; Organizations</Link>
        <span aria-hidden="true"> / </span>
        <span aria-current="page">{record.authorized_name}</span>
      </nav>

      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">{record.authorized_name}</h1>
      <div className="mb-6 flex items-center gap-3">
        <span className="text-sm text-gray-600 dark:text-gray-400">{typeLabels[record.entity_type] ?? record.entity_type}</span>
        {record.dates && <span className="text-sm text-gray-500 dark:text-gray-400">{record.dates}</span>}
        {record.is_public && <span className="text-xs text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/30 rounded px-2 py-0.5">Public</span>}
        {record.wikidata_qid && <span className="text-xs text-purple-700 dark:text-purple-400 bg-purple-50 dark:bg-purple-900/30 rounded px-2 py-0.5">Wikidata: {record.wikidata_qid}</span>}
      </div>

      <div className="space-y-6">
        {record.biographical_history && (
          <section aria-labelledby="bio-heading">
            <h2 id="bio-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Biographical History</h2>
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{record.biographical_history}</div>
          </section>
        )}
        {record.administrative_history && (
          <section aria-labelledby="admin-hist-heading">
            <h2 id="admin-hist-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Administrative History</h2>
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-sm text-gray-700 dark:text-gray-300 leading-relaxed whitespace-pre-wrap">{record.administrative_history}</div>
          </section>
        )}
        {record.variant_names && (
          <section aria-labelledby="variants-heading">
            <h2 id="variants-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Variant Names</h2>
            <ul className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-1">
              {record.variant_names.split('|').map((name, i) => <li key={i} className="text-sm text-gray-700 dark:text-gray-300">{name.trim()}</li>)}
            </ul>
          </section>
        )}

        <section aria-labelledby="docs-heading">
          <h2 id="docs-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Linked Documents</h2>
          {documentsQuery.isLoading && <Spinner size="sm" label="Loading documents" />}
          {documentsQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load documents.</p>}
          {documentsQuery.data && Array.isArray(documentsQuery.data) && documentsQuery.data.length === 0 && (
            <p className="text-gray-500 dark:text-gray-400 text-sm">No documents linked to this record.</p>
          )}
          {documentsQuery.data && Array.isArray(documentsQuery.data) && documentsQuery.data.length > 0 && (
            <ul className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
              {documentsQuery.data.map((doc: Document) => (
                <li key={doc.id} className="px-4 py-3">
                  <Link to={`/archive/documents/${doc.id}`}
                    className="text-blue-700 dark:text-blue-400 hover:underline font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                    {doc.title}
                  </Link>
                  {doc.date_display && <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">{doc.date_display}</span>}
                </li>
              ))}
            </ul>
          )}
        </section>

        <section aria-labelledby="events-heading">
          <h2 id="events-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Linked Events</h2>
          {eventsQuery.isLoading && <Spinner size="sm" label="Loading events" />}
          {eventsQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load events.</p>}
          {eventsQuery.data && Array.isArray(eventsQuery.data) && eventsQuery.data.length === 0 && (
            <p className="text-gray-500 dark:text-gray-400 text-sm">No events linked to this record.</p>
          )}
          {eventsQuery.data && Array.isArray(eventsQuery.data) && eventsQuery.data.length > 0 && (
            <ul className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg divide-y divide-gray-100 dark:divide-gray-700">
              {(eventsQuery.data as Array<{ id: number; title: string; date_display?: string }>).map((evt) => (
                <li key={evt.id} className="px-4 py-3">
                  <Link to={`/events/${evt.id}`}
                    className="text-blue-700 dark:text-blue-400 hover:underline font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                    {evt.title}
                  </Link>
                  {evt.date_display && <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">{evt.date_display}</span>}
                </li>
              ))}
            </ul>
          )}
        </section>

        {record.notes && (
          <section aria-labelledby="notes-heading">
            <h2 id="notes-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">Notes</h2>
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{record.notes}</div>
          </section>
        )}
      </div>
    </div>
  );
}
