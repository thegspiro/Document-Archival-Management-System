/**
 * Authority record detail: biography/history, linked documents, relationships,
 * events, and Wikidata enrichment information.
 */
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { authorityApi } from '../api/authority';
import apiClient from '../api/client';
import type { AuthorityRecord } from '../types/api';

export default function PersonDetailPage() {
  const { id } = useParams<{ id: string }>();
  const authorityId = Number(id);

  const recordQuery = useQuery<AuthorityRecord>({
    queryKey: ['authority', authorityId],
    queryFn: () => authorityApi.get(authorityId),
    enabled: !isNaN(authorityId),
  });

  const docsQuery = useQuery({
    queryKey: ['authority-docs', authorityId],
    queryFn: () => authorityApi.getDocuments(authorityId),
    enabled: !isNaN(authorityId),
  });

  const relQuery = useQuery({
    queryKey: ['authority-relationships', authorityId],
    queryFn: () => apiClient.get(`/authority/${authorityId}/relationships`).then((r) => r.data),
    enabled: !isNaN(authorityId),
  });

  const eventsQuery = useQuery({
    queryKey: ['authority-events', authorityId],
    queryFn: () => apiClient.get(`/authority/${authorityId}/events`).then((r) => r.data),
    enabled: !isNaN(authorityId),
  });

  const record = recordQuery.data;

  if (recordQuery.isLoading) {
    return (
      <div role="status" aria-label="Loading authority record" className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent" aria-hidden="true" />
        <span className="ml-3 text-gray-500 dark:text-gray-400">Loading authority record...</span>
      </div>
    );
  }

  if (recordQuery.isError || !record) {
    return (
      <div role="alert" className="p-6 max-w-3xl mx-auto">
        <div className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
          Authority record not found or failed to load.
        </div>
      </div>
    );
  }

  const wikidata = record.wikidata_enrichment as Record<string, string> | null;

  return (
    <div className="max-w-7xl mx-auto p-6">
      <nav className="mb-4" aria-label="Breadcrumb">
        <Link to="/people" className="text-sm text-blue-600 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
          &larr; Back to Authority Records
        </Link>
      </nav>

      <div className="flex items-start justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{record.authorized_name}</h1>
          <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
            <span className="capitalize">{record.entity_type}</span>
            {record.dates && <span> &middot; {record.dates}</span>}
            {record.identifier && <span> &middot; {record.identifier}</span>}
          </p>
        </div>
        <Link
          to={`/people/${record.id}/edit`}
          className="min-h-[44px] inline-flex items-center px-4 py-2 rounded-md bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2"
        >
          Edit
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main content */}
        <section className="lg:col-span-2 space-y-6">
          {/* Biography */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">
              {record.entity_type === 'organization' ? 'Administrative History' : 'Biographical History'}
            </h2>
            <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">
              {(record.entity_type === 'organization' ? record.administrative_history : record.biographical_history) ?? 'No history recorded.'}
            </p>
            {record.variant_names && (
              <div className="mt-3">
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Variant Names</p>
                <p className="text-sm text-gray-700 dark:text-gray-300">{record.variant_names.replace(/\|/g, ', ')}</p>
              </div>
            )}
            {record.notes && (
              <div className="mt-3">
                <p className="text-xs font-medium text-gray-500 dark:text-gray-400 uppercase">Notes</p>
                <p className="text-sm text-gray-700 dark:text-gray-300 whitespace-pre-wrap">{record.notes}</p>
              </div>
            )}
          </div>

          {/* Linked Documents */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Linked Documents</h2>
            {docsQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">Loading...</p>}
            {docsQuery.data && Array.isArray(docsQuery.data) && docsQuery.data.length > 0 ? (
              <ul className="divide-y divide-gray-100 dark:divide-gray-700">
                {(docsQuery.data as Array<{ id: number; title: string; accession_number?: string; date_display?: string }>).map((doc) => (
                  <li key={doc.id} className="py-2">
                    <Link to={`/archive/documents/${doc.id}`} className="text-blue-700 dark:text-blue-400 hover:underline text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                      {doc.title}
                    </Link>
                    <p className="text-xs text-gray-400 dark:text-gray-500">
                      {doc.accession_number}{doc.date_display && ` \u00b7 ${doc.date_display}`}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              !docsQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">No linked documents.</p>
            )}
          </div>

          {/* Events */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Events</h2>
            {eventsQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">Loading...</p>}
            {eventsQuery.data && Array.isArray(eventsQuery.data) && eventsQuery.data.length > 0 ? (
              <ul className="divide-y divide-gray-100 dark:divide-gray-700">
                {(eventsQuery.data as Array<{ id: number; event: { id: number; title: string; date_display?: string }; role: { term: string } }>).map((link) => (
                  <li key={link.id} className="py-2">
                    <Link to={`/events/${link.event.id}`} className="text-blue-700 dark:text-blue-400 hover:underline text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                      {link.event.title}
                    </Link>
                    <span className="text-xs text-gray-400 dark:text-gray-500 ml-1">({link.role.term})</span>
                  </li>
                ))}
              </ul>
            ) : (
              !eventsQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">No linked events.</p>
            )}
          </div>
        </section>

        {/* Sidebar */}
        <aside className="space-y-6">
          {/* Relationships */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Relationships</h2>
            {relQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">Loading...</p>}
            {relQuery.data && Array.isArray(relQuery.data) && relQuery.data.length > 0 ? (
              <ul className="space-y-2">
                {(relQuery.data as Array<{ id: number; target_authority: { id: number; authorized_name: string }; relationship_type: { term: string } }>).map((rel) => (
                  <li key={rel.id} className="text-sm">
                    <span className="text-gray-500 dark:text-gray-400 capitalize">{rel.relationship_type.term.replace(/_/g, ' ')}</span>{' '}
                    <Link to={`/people/${rel.target_authority.id}`} className="text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                      {rel.target_authority.authorized_name}
                    </Link>
                  </li>
                ))}
              </ul>
            ) : (
              !relQuery.isLoading && <p className="text-sm text-gray-500 dark:text-gray-400">No relationships.</p>
            )}
          </div>

          {/* Wikidata */}
          <div className="rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Wikidata</h2>
            {record.wikidata_qid ? (
              <div className="space-y-2 text-sm">
                <p>
                  <span className="font-medium text-gray-700 dark:text-gray-300">QID:</span>{' '}
                  <a
                    href={`https://www.wikidata.org/wiki/${record.wikidata_qid}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded"
                  >
                    {record.wikidata_qid}
                  </a>
                </p>
                {wikidata?.description && <p className="text-gray-600 dark:text-gray-400">{wikidata.description}</p>}
                {wikidata?.occupation && <p><span className="font-medium text-gray-700 dark:text-gray-300">Occupation:</span> {wikidata.occupation}</p>}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400">Not linked to Wikidata.</p>
            )}
          </div>
        </aside>
      </div>
    </div>
  );
}
