/**
 * Document detail view with tabs for metadata, files, and relationships.
 * Displays ISAD(G) fields, file viewer, OCR status, and version panel.
 */
import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { documentsApi } from '../../api/documents';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import type { Document, DocumentFile } from '../../types/api';

type TabKey = 'metadata' | 'files' | 'relationships' | 'annotations';

function CompletenessBadge({ level }: { level: string }) {
  const styles: Record<string, string> = {
    none: 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300',
    minimal: 'bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200',
    standard: 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200',
    full: 'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-200',
  };
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${styles[level] ?? styles.none}`}
      role="img"
      aria-label={`Description completeness: ${level}`}
    >
      {level}
    </span>
  );
}

function MetadataField({ label, value }: { label: string; value: string | null | undefined }) {
  if (!value) return null;
  return (
    <div className="py-2 border-b border-gray-100 dark:border-gray-700">
      <dt className="text-sm font-medium text-gray-500 dark:text-gray-400">{label}</dt>
      <dd className="mt-1 text-sm text-gray-900 dark:text-gray-100">{value}</dd>
    </div>
  );
}

function FileCard({ file, documentId }: { file: DocumentFile; documentId: number }) {
  const ocrStatusColors: Record<string, string> = {
    none: 'bg-gray-100 text-gray-600 dark:bg-gray-700 dark:text-gray-400',
    queued: 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300',
    processing: 'bg-blue-100 text-blue-700 dark:bg-blue-900/40 dark:text-blue-300',
    complete: 'bg-green-100 text-green-700 dark:bg-green-900/40 dark:text-green-300',
    failed: 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300',
  };

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
      <div className="flex items-start justify-between">
        <div>
          <p className="font-medium text-gray-900 dark:text-gray-100">{file.filename}</p>
          <p className="text-sm text-gray-500 dark:text-gray-400">
            {file.mime_type ?? 'Unknown type'}
            {file.file_size_bytes != null && ` \u00b7 ${(file.file_size_bytes / 1024).toFixed(1)} KB`}
            {file.page_count > 1 && ` \u00b7 ${file.page_count} pages`}
          </p>
        </div>
        <a
          href={`/api/v1/documents/${documentId}/files/${file.id}/download`}
          className="min-h-[44px] inline-flex items-center px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
          download
        >
          Download
        </a>
      </div>
      <div className="mt-3 flex items-center gap-2">
        <span className="text-xs text-gray-500 dark:text-gray-400">OCR:</span>
        <span className={`text-xs px-2 py-0.5 rounded ${ocrStatusColors[file.ocr_status] ?? ocrStatusColors.none}`}>
          {file.ocr_status}
        </span>
        {file.ocr_status === 'failed' && file.ocr_error && (
          <span role="alert" className="text-xs text-red-600 dark:text-red-400">
            {file.ocr_error}
          </span>
        )}
      </div>
      {file.format_name && (
        <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
          Format: {file.format_name}{file.format_puid ? ` (${file.format_puid})` : ''}
        </p>
      )}
      {file.preservation_warning && (
        <p className="mt-2 text-xs text-amber-600 dark:text-amber-400">
          Warning: {file.preservation_warning}
        </p>
      )}
    </div>
  );
}

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [activeTab, setActiveTab] = useState<TabKey>('metadata');
  const documentId = Number(id);

  const { data: doc, isLoading, isError } = useQuery<Document>({
    queryKey: ['documents', documentId],
    queryFn: () => documentsApi.get(documentId),
    enabled: !Number.isNaN(documentId),
  });

  const relationshipsQuery = useQuery({
    queryKey: ['documents', documentId, 'relationships'],
    queryFn: () => apiClient.get(`/documents/${documentId}/relationships`).then((r) => r.data),
    enabled: activeTab === 'relationships' && !Number.isNaN(documentId),
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner label="Loading document" />
      </div>
    );
  }

  if (isError || !doc) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
          Failed to load document. It may not exist or you may lack permission.
        </div>
        <Link to="/archive" className="mt-4 inline-block text-blue-700 dark:text-blue-400 hover:underline">
          Back to archive
        </Link>
      </div>
    );
  }

  const tabs: { key: TabKey; label: string }[] = [
    { key: 'metadata', label: 'Metadata' },
    { key: 'files', label: `Files (${doc.files?.length ?? 0})` },
    { key: 'relationships', label: 'Relationships' },
    { key: 'annotations', label: 'Annotations' },
  ];

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-start justify-between mb-6">
        <div>
          <nav aria-label="Breadcrumb" className="text-sm text-gray-500 dark:text-gray-400 mb-2">
            <Link to="/archive" className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
              Archive
            </Link>
            <span aria-hidden="true"> / </span>
            <span aria-current="page">{doc.accession_number ?? `Document #${doc.id}`}</span>
          </nav>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">{doc.title}</h1>
          <div className="mt-2 flex items-center gap-3">
            {doc.accession_number && (
              <span className="text-sm text-gray-600 dark:text-gray-400">{doc.accession_number}</span>
            )}
            <CompletenessBadge level={doc.description_completeness} />
            <span className="text-xs capitalize text-gray-500 dark:text-gray-400 border border-gray-200 dark:border-gray-600 rounded px-2 py-0.5">
              {doc.description_status}
            </span>
            {doc.is_public && (
              <span className="text-xs text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/30 rounded px-2 py-0.5">
                Public
              </span>
            )}
          </div>
        </div>
        <Link
          to={`/archive/documents/${doc.id}/edit`}
          className="min-h-[44px] inline-flex items-center px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2"
        >
          Edit
        </Link>
      </div>

      {/* Content Advisory */}
      {doc.has_content_advisory && (
        <div className="mb-6 p-4 rounded bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200" role="alert">
          <p className="font-medium">Content Advisory</p>
          <p className="mt-1 text-sm">
            {doc.content_advisory_note ??
              'This item may contain language or content that reflects historical attitudes that are harmful or offensive to modern readers.'}
          </p>
        </div>
      )}

      {/* Version Panel */}
      {doc.version_group_id != null && (
        <div className="mb-6 p-4 bg-gray-50 dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg">
          <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
            Version {doc.version_number}
            {doc.version_label && <span> &mdash; {doc.version_label}</span>}
            {doc.is_canonical_version && (
              <span className="ml-2 text-xs bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300 rounded px-2 py-0.5">
                Canonical
              </span>
            )}
          </p>
        </div>
      )}

      {/* Tabs */}
      <div role="tablist" aria-label="Document sections" className="border-b border-gray-200 dark:border-gray-700 mb-6">
        <div className="flex gap-0">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              role="tab"
              aria-selected={activeTab === tab.key}
              aria-controls={`tabpanel-${tab.key}`}
              id={`tab-${tab.key}`}
              onClick={() => setActiveTab(tab.key)}
              className={`min-h-[44px] px-4 py-2 text-sm font-medium border-b-2 transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2 ${
                activeTab === tab.key
                  ? 'border-blue-600 text-blue-700 dark:text-blue-400'
                  : 'border-transparent text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab Panels */}
      <div
        id="tabpanel-metadata"
        role="tabpanel"
        aria-labelledby="tab-metadata"
        hidden={activeTab !== 'metadata'}
      >
        <dl className="space-y-0">
          <MetadataField label="Title" value={doc.title} />
          <MetadataField label="Reference Code" value={doc.reference_code} />
          <MetadataField label="Date" value={doc.date_display} />
          <MetadataField label="Level of Description" value={doc.level_of_description} />
          <MetadataField label="Extent" value={doc.extent} />
          <MetadataField label="Creator" value={doc.creator?.authorized_name} />
          <MetadataField label="Scope and Content" value={doc.scope_and_content} />
          <MetadataField label="Access Conditions" value={doc.access_conditions} />
          <MetadataField label="Language" value={doc.language_of_material} />
          <MetadataField label="Copyright Status" value={doc.copyright_status} />
          <MetadataField label="Rights Holder" value={doc.rights_holder} />
          <MetadataField label="Rights Note" value={doc.rights_note} />
          <MetadataField label="Location" value={doc.geo_location_name} />
          {doc.ark_id && <MetadataField label="ARK Identifier" value={doc.ark_id} />}
        </dl>
        {doc.terms && doc.terms.length > 0 && (
          <div className="mt-6">
            <h3 className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-2">Tags</h3>
            <div className="flex flex-wrap gap-2">
              {doc.terms.map((dt) => (
                <span
                  key={dt.id}
                  className="inline-block px-2 py-1 text-xs rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
                >
                  {dt.term.term}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>

      <div
        id="tabpanel-files"
        role="tabpanel"
        aria-labelledby="tab-files"
        hidden={activeTab !== 'files'}
      >
        {doc.files && doc.files.length > 0 ? (
          <div className="space-y-4">
            {doc.files.map((file) => (
              <FileCard key={file.id} file={file} documentId={doc.id} />
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400 text-sm py-4">
            No files attached to this document.
          </p>
        )}
      </div>

      <div
        id="tabpanel-relationships"
        role="tabpanel"
        aria-labelledby="tab-relationships"
        hidden={activeTab !== 'relationships'}
      >
        {relationshipsQuery.isLoading && <Spinner size="sm" label="Loading relationships" />}
        {relationshipsQuery.isError && (
          <p className="text-red-600 dark:text-red-400 text-sm">Failed to load relationships.</p>
        )}
        {relationshipsQuery.data && Array.isArray(relationshipsQuery.data) && relationshipsQuery.data.length === 0 && (
          <p className="text-gray-500 dark:text-gray-400 text-sm py-4">
            No relationships defined. Use the edit page to add relationships.
          </p>
        )}
        {relationshipsQuery.data && Array.isArray(relationshipsQuery.data) && relationshipsQuery.data.length > 0 && (
          <ul className="divide-y divide-gray-100 dark:divide-gray-700">
            {relationshipsQuery.data.map((rel: Record<string, unknown>) => (
              <li key={rel.id as number} className="py-3 flex items-center justify-between">
                <div>
                  <span className="text-sm text-gray-900 dark:text-gray-100">
                    {(rel.target_document as Record<string, unknown>)?.title as string ?? `Document #${rel.target_document_id as number}`}
                  </span>
                  <span className="ml-2 text-xs text-gray-500 dark:text-gray-400">
                    ({(rel.relationship_type as Record<string, unknown>)?.term as string ?? 'related'})
                  </span>
                </div>
                <Link
                  to={`/archive/documents/${rel.target_document_id as number}`}
                  className="text-sm text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded"
                >
                  View
                </Link>
              </li>
            ))}
          </ul>
        )}
      </div>

      <div
        id="tabpanel-annotations"
        role="tabpanel"
        aria-labelledby="tab-annotations"
        hidden={activeTab !== 'annotations'}
      >
        <p className="text-gray-500 dark:text-gray-400 text-sm py-4">
          Annotations are available in the document file viewer. Select a file above to view or create annotations.
        </p>
      </div>
    </div>
  );
}
