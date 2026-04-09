/**
 * Vertical timeline component for chronological display of documents.
 * Renders documents along a vertical line with date markers, thumbnails,
 * and optional description excerpts. Used by the exhibition block renderer
 * for 'timeline' block types.
 */
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';
import type { Document } from '../../types/api';
import Spinner from './Spinner';

interface TimelineDocument {
  id: number;
  title: string;
  date_display: string | null;
  date_start: string | null;
  scope_and_content: string | null;
  thumbnail_url: string | null;
}

interface TimelineBlockProps {
  /** Explicit list of document IDs to display. */
  documentIds?: number[];
  /** Dynamic query parameters to fetch documents. */
  query?: {
    term_ids?: number[];
    node_id?: number;
    date_from?: string;
    date_to?: string;
  };
  /** Which document field to use as the timeline entry label. */
  titleField?: 'title' | string;
  /** Which date field to use for ordering and display. */
  dateField?: 'date_start' | 'date_display';
  /** Whether to show description excerpts below each entry. */
  showDescriptions?: boolean;
}

function buildQueryParams(
  documentIds?: number[],
  query?: TimelineBlockProps['query'],
): Record<string, string | number> {
  const params: Record<string, string | number> = {
    is_public: 1,
    per_page: 100,
  };

  if (documentIds && documentIds.length > 0) {
    params.ids = documentIds.join(',');
  }

  if (query) {
    if (query.term_ids && query.term_ids.length > 0) {
      params.term_ids = query.term_ids.join(',');
    }
    if (query.node_id) {
      params.node_id = query.node_id;
    }
    if (query.date_from) {
      params.date_from = query.date_from;
    }
    if (query.date_to) {
      params.date_to = query.date_to;
    }
  }

  return params;
}

function toTimelineDoc(doc: Document): TimelineDocument {
  const firstFile = doc.files?.[0];
  const thumbnailUrl = firstFile?.thumbnail_path
    ? `/api/v1/public/documents/${doc.id}/files/${firstFile.id}/thumbnail`
    : null;

  return {
    id: doc.id,
    title: doc.title,
    date_display: doc.date_display,
    date_start: doc.date_start,
    scope_and_content: doc.scope_and_content,
    thumbnail_url: thumbnailUrl,
  };
}

function truncateText(text: string, maxLength: number): string {
  if (text.length <= maxLength) return text;
  const truncated = text.slice(0, maxLength);
  const lastSpace = truncated.lastIndexOf(' ');
  return (lastSpace > 0 ? truncated.slice(0, lastSpace) : truncated) + '\u2026';
}

function formatDate(doc: TimelineDocument, dateField: string): string {
  if (dateField === 'date_display' && doc.date_display) {
    return doc.date_display;
  }
  if (doc.date_start) {
    return doc.date_start;
  }
  if (doc.date_display) {
    return doc.date_display;
  }
  return 'Date unknown';
}

function sortByDate(docs: TimelineDocument[], dateField: string): TimelineDocument[] {
  return [...docs].sort((a, b) => {
    const dateA = dateField === 'date_start' ? a.date_start : a.date_display;
    const dateB = dateField === 'date_start' ? b.date_start : b.date_display;

    if (!dateA && !dateB) return 0;
    if (!dateA) return 1;
    if (!dateB) return -1;

    return dateA.localeCompare(dateB);
  });
}

export default function TimelineBlock({
  documentIds,
  query,
  titleField: _titleField = 'title',
  dateField = 'date_start',
  showDescriptions = false,
}: TimelineBlockProps) {
  // _titleField is accepted for API contract parity; the rendered label
  // always uses the document title. Reserved for future field expansion.
  const params = buildQueryParams(documentIds, query);

  const {
    data,
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: ['public-timeline-documents', documentIds, query],
    queryFn: () =>
      apiClient
        .get<{ items: Document[] }>('/public/search', { params })
        .then((r) => r.data),
    enabled:
      (documentIds !== undefined && documentIds.length > 0) ||
      query !== undefined,
  });

  if (isLoading) {
    return (
      <div className="py-8">
        <Spinner label="Loading timeline" />
      </div>
    );
  }

  if (isError) {
    return (
      <div
        className="py-8 text-center text-[var(--color-error)]"
        role="alert"
      >
        <p>Failed to load timeline content.</p>
        <p className="text-sm text-[var(--color-text-muted)] mt-1">
          {error instanceof Error ? error.message : 'An unexpected error occurred.'}
        </p>
      </div>
    );
  }

  const documents = data?.items ?? [];

  if (documents.length === 0) {
    return (
      <div className="py-8 text-center text-[var(--color-text-muted)]">
        <p>No documents available for this timeline.</p>
      </div>
    );
  }

  const timelineDocs = sortByDate(documents.map(toTimelineDoc), dateField);

  return (
    <section aria-label="Document timeline">
      <ol
        className="relative ml-4 border-l-2 border-gray-300 dark:border-gray-600"
        aria-label="Chronological list of documents"
      >
        {timelineDocs.map((doc, index) => (
          <li key={doc.id} className="mb-8 ml-6 last:mb-0">
            {/* Timeline dot marker */}
            <span
              className="absolute -left-[9px] flex h-4 w-4 items-center justify-center rounded-full bg-[var(--color-link)] ring-4 ring-white dark:ring-gray-900"
              aria-hidden="true"
            />

            <article
              className="rounded-lg border border-[var(--color-border)] bg-white p-4 shadow-sm dark:bg-gray-800"
              aria-posinset={index + 1}
              aria-setsize={timelineDocs.length}
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
                {/* Thumbnail */}
                {doc.thumbnail_url && (
                  <div className="flex-shrink-0">
                    <a
                      href={`/public/documents/${doc.id}`}
                      aria-label={`View ${doc.title}`}
                    >
                      <img
                        src={doc.thumbnail_url}
                        alt=""
                        className="h-20 w-20 rounded object-cover"
                        loading="lazy"
                      />
                    </a>
                  </div>
                )}

                <div className="min-w-0 flex-1">
                  {/* Date */}
                  <time
                    className="mb-1 block text-sm font-medium text-[var(--color-text-muted)]"
                    dateTime={doc.date_start ?? undefined}
                  >
                    {formatDate(doc, dateField)}
                  </time>

                  {/* Title — titleField is reserved for future field expansion */}
                  <h3 className="text-base font-semibold text-[var(--color-text-primary)]">
                    <a
                      href={`/public/documents/${doc.id}`}
                      className="text-[var(--color-link)] underline hover:text-[var(--color-link-visited)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)]"
                    >
                      {doc.title}
                    </a>
                  </h3>

                  {/* Description excerpt */}
                  {showDescriptions && doc.scope_and_content && (
                    <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
                      {truncateText(doc.scope_and_content, 200)}
                    </p>
                  )}
                </div>
              </div>
            </article>
          </li>
        ))}
      </ol>
    </section>
  );
}
