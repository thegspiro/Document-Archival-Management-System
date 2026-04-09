/**
 * Public document view. Shows document metadata, file viewer, citation widget,
 * and schema.org structured data derived from the Dublin Core crosswalk.
 */
import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import { generateDocumentLD } from '../../utils/structuredData';
import { useInstitution } from '../../context/InstitutionContext';
import type { Document } from '../../types/api';

const CITATION_FORMATS = [
  { value: 'chicago_note', label: 'Chicago (Note)' },
  { value: 'chicago_bib', label: 'Chicago (Bibliography)' },
  { value: 'turabian', label: 'Turabian' },
  { value: 'bibtex', label: 'BibTeX' },
  { value: 'ris', label: 'RIS' },
];

export default function PublicDocumentPage() {
  const { id } = useParams<{ id: string }>();
  const documentId = Number(id);
  const [citationFormat, setCitationFormat] = useState('chicago_note');
  const institution = useInstitution();

  const { data: doc, isLoading, isError } = useQuery<Document>({
    queryKey: ['public', 'documents', documentId],
    queryFn: () => apiClient.get(`/public/documents/${documentId}`).then((r) => r.data),
    enabled: !Number.isNaN(documentId),
  });

  const citationQuery = useQuery<string>({
    queryKey: ['public', 'documents', documentId, 'cite', citationFormat],
    queryFn: () => apiClient.get(`/documents/${documentId}/cite`, { params: { format: citationFormat } }).then((r) => r.data),
    enabled: !Number.isNaN(documentId) && !!doc,
  });

  if (isLoading) return <div className="flex justify-center py-16"><Spinner label="Loading document" /></div>;

  if (isError || !doc) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
          This document is not available. It may not exist or may not be publicly accessible.
        </div>
        <Link to="/public/search" className="mt-4 inline-block text-blue-700 dark:text-blue-400 hover:underline">Search documents</Link>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* Content Advisory */}
      {doc.has_content_advisory && (
        <div className="mb-6 p-4 rounded bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-800 text-amber-800 dark:text-amber-200" role="alert">
          <p className="font-medium">Content Advisory</p>
          <p className="mt-1 text-sm">
            {doc.content_advisory_note ?? 'This item may contain language or content that reflects historical attitudes that are harmful or offensive to modern readers.'}
          </p>
        </div>
      )}

      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">{doc.title}</h1>
      <div className="flex flex-wrap items-center gap-3 mb-6 text-sm text-gray-600 dark:text-gray-400">
        {doc.date_display && <span>{doc.date_display}</span>}
        {doc.creator && <span>by {doc.creator.authorized_name}</span>}
        {doc.accession_number && <span className="font-mono text-xs">{doc.accession_number}</span>}
      </div>

      {/* File viewer placeholder */}
      {doc.files && doc.files.length > 0 && (
        <section aria-labelledby="viewer-heading" className="mb-8">
          <h2 id="viewer-heading" className="sr-only">Document files</h2>
          <div className="bg-gray-100 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-8 text-center" role="region" aria-label={`Document viewer: ${doc.title}`}>
            <p className="text-gray-500 dark:text-gray-400 mb-4">{doc.files.length} file{doc.files.length !== 1 ? 's' : ''} available</p>
            {doc.files.map((file) => (
              <div key={file.id} className="mb-2">
                <a href={`/api/v1/public/documents/${doc.id}/files/${file.id}`}
                  className="text-blue-700 dark:text-blue-400 hover:underline text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                  {file.filename} ({file.mime_type ?? 'file'})
                </a>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Metadata */}
      <section aria-labelledby="metadata-heading" className="mb-8">
        <h2 id="metadata-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Metadata</h2>
        <dl className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-3">
          {doc.extent && <div><dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Extent</dt><dd className="text-sm text-gray-900 dark:text-gray-100">{doc.extent}</dd></div>}
          {doc.scope_and_content && <div><dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Scope and Content</dt><dd className="text-sm text-gray-900 dark:text-gray-100 whitespace-pre-wrap">{doc.scope_and_content}</dd></div>}
          {doc.language_of_material && <div><dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Language</dt><dd className="text-sm text-gray-900 dark:text-gray-100">{doc.language_of_material}</dd></div>}
          {doc.access_conditions && <div><dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Access Conditions</dt><dd className="text-sm text-gray-900 dark:text-gray-100">{doc.access_conditions}</dd></div>}
          {doc.copyright_status && <div><dt className="text-sm font-medium text-gray-500 dark:text-gray-400">Copyright</dt><dd className="text-sm text-gray-900 dark:text-gray-100 capitalize">{doc.copyright_status.replace(/_/g, ' ')}</dd></div>}
        </dl>
      </section>

      {/* Tags */}
      {doc.terms && doc.terms.length > 0 && (
        <section aria-labelledby="tags-heading" className="mb-8">
          <h2 id="tags-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Tags</h2>
          <div className="flex flex-wrap gap-2">
            {doc.terms.map((dt) => (
              <span key={dt.id} className="inline-block px-3 py-1 text-sm rounded bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300">{dt.term.term}</span>
            ))}
          </div>
        </section>
      )}

      {/* Citation */}
      <section aria-labelledby="cite-heading" className="mb-8">
        <h2 id="cite-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Cite This Document</h2>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
          <div className="mb-3">
            <label htmlFor="citation-format" className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Format</label>
            <select id="citation-format" value={citationFormat} onChange={(e) => setCitationFormat(e.target.value)}
              className="min-h-[44px] rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]">
              {CITATION_FORMATS.map((fmt) => <option key={fmt.value} value={fmt.value}>{fmt.label}</option>)}
            </select>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900 rounded p-3 text-sm text-gray-700 dark:text-gray-300 font-mono">
            {citationQuery.isLoading && <span className="text-gray-400">Loading citation...</span>}
            {citationQuery.isError && <span className="text-red-600 dark:text-red-400">Failed to generate citation.</span>}
            {citationQuery.data && <p>{citationQuery.data}</p>}
          </div>
        </div>
      </section>

      {/* Schema.org structured data — derived from Dublin Core crosswalk (CLAUDE.md section 22) */}
      <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(
        generateDocumentLD(doc, institution.name)
      ) }} />
    </div>
  );
}
