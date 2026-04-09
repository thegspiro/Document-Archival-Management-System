/**
 * Main exhibition block renderer. Accepts a block object from the exhibition
 * page API response and renders the appropriate sub-component based on block_type.
 * Each block type handles its own data fetching, loading, and error states.
 *
 * Supports all block types defined in CLAUDE.md section 12.5:
 * html, file_with_text, gallery, document_metadata, map, timeline,
 * table_of_contents, collection_browse, separator.
 */
import React, { Component, Suspense, type ErrorInfo, type ReactNode } from 'react';
import { useQuery } from '@tanstack/react-query';
import DOMPurify from 'dompurify';
import apiClient from '../../api/client';
import type {
  Document,
  ExhibitionPage,
  ExhibitionPageBlock,
  PaginatedResponse,
} from '../../types/api';
import Spinner from './Spinner';
import TimelineBlock from './TimelineBlock';

/**
 * Lazy-load MapBlock so Leaflet is only bundled when a map block is rendered.
 * Falls back gracefully if MapBlock.tsx does not yet exist at build time.
 */
const LazyMapBlock = React.lazy(() => import('./MapBlock'));

/* -------------------------------------------------------------------------- */
/*  Props                                                                      */
/* -------------------------------------------------------------------------- */

interface ExhibitionBlockRendererProps {
  block: ExhibitionPageBlock;
  /** Exhibition slug, used for building page links in table_of_contents. */
  exhibitionSlug?: string;
  /** Full page tree for the exhibition, required by table_of_contents blocks. */
  pages?: ExhibitionPage[];
}

/* -------------------------------------------------------------------------- */
/*  Layout wrapper                                                             */
/* -------------------------------------------------------------------------- */

const layoutClasses: Record<string, string> = {
  full: 'w-full',
  left: 'sm:float-left sm:w-1/2 sm:mr-6 sm:mb-4 w-full',
  right: 'sm:float-right sm:w-1/2 sm:ml-6 sm:mb-4 w-full',
  center: 'mx-auto w-full sm:w-3/4',
};

function BlockLayout({
  layout,
  children,
}: {
  layout: string;
  children: React.ReactNode;
}) {
  const cls = layoutClasses[layout] ?? layoutClasses.full;
  return <div className={`mb-8 ${cls}`}>{children}</div>;
}

/* -------------------------------------------------------------------------- */
/*  Error fallback                                                             */
/* -------------------------------------------------------------------------- */

function BlockError({ message }: { message: string }) {
  return (
    <div
      className="rounded-md border border-[var(--color-error)] bg-red-50 p-4 text-sm text-[var(--color-error)] dark:bg-red-900/20"
      role="alert"
    >
      <p>{message}</p>
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Shared data-fetching helpers                                               */
/* -------------------------------------------------------------------------- */

function usePublicDocument(documentId: number | undefined) {
  return useQuery({
    queryKey: ['public-document', documentId],
    queryFn: () =>
      apiClient
        .get<Document>(`/public/documents/${documentId}`)
        .then((r) => r.data),
    enabled: documentId !== undefined && documentId > 0,
  });
}

function usePublicDocuments(documentIds: number[] | undefined) {
  return useQuery({
    queryKey: ['public-documents-batch', documentIds],
    queryFn: () =>
      apiClient
        .get<{ items: Document[] }>('/public/search', {
          params: {
            ids: documentIds!.join(','),
            per_page: documentIds!.length,
            is_public: 1,
          },
        })
        .then((r) => r.data),
    enabled: documentIds !== undefined && documentIds.length > 0,
  });
}

function useCollectionDocuments(
  nodeId: number | undefined,
  perPage: number,
) {
  return useQuery({
    queryKey: ['public-collection-documents', nodeId, perPage],
    queryFn: () =>
      apiClient
        .get<PaginatedResponse<Document>>('/public/search', {
          params: { node_id: nodeId, per_page: perPage, is_public: 1 },
        })
        .then((r) => r.data),
    enabled: nodeId !== undefined && nodeId > 0,
  });
}

function thumbnailUrl(doc: Document, fileId?: number): string | null {
  const file = fileId
    ? doc.files?.find((f) => f.id === fileId)
    : doc.files?.[0];
  if (!file?.thumbnail_path) return null;
  return `/api/v1/public/documents/${doc.id}/files/${file.id}/thumbnail`;
}

/* -------------------------------------------------------------------------- */
/*  Block: html                                                                */
/* -------------------------------------------------------------------------- */

function HtmlBlock({ content }: { content: { html?: string } }) {
  const rawHtml = content.html ?? '';
  const cleanHtml = DOMPurify.sanitize(rawHtml, {
    USE_PROFILES: { html: true },
    ADD_ATTR: ['target'],
  });

  return (
    <div
      className="prose prose-stone max-w-none dark:prose-invert"
      // DOMPurify sanitizes the HTML to prevent XSS before rendering.
      dangerouslySetInnerHTML={{ __html: cleanHtml }}
    />
  );
}

/* -------------------------------------------------------------------------- */
/*  Block: file_with_text                                                      */
/* -------------------------------------------------------------------------- */

interface FileWithTextContent {
  document_id?: number;
  file_id?: number;
  caption?: string;
  text_html?: string;
  image_position?: 'left' | 'right';
}

function FileWithTextBlock({ content }: { content: FileWithTextContent }) {
  const { data: doc, isLoading, isError } = usePublicDocument(content.document_id);

  if (isLoading) {
    return <Spinner label="Loading document" />;
  }

  if (isError || !doc) {
    return <BlockError message="Unable to load document for this block." />;
  }

  const imgSrc = thumbnailUrl(doc, content.file_id);
  const cleanHtml = DOMPurify.sanitize(content.text_html ?? '', {
    USE_PROFILES: { html: true },
  });

  const imageOnLeft = content.image_position !== 'right';

  const imageElement = imgSrc ? (
    <div className="flex-shrink-0 sm:w-1/2">
      <a
        href={`/public/documents/${doc.id}`}
        aria-label={`View document: ${doc.title}`}
      >
        <img
          src={imgSrc}
          alt={`${doc.title}${content.caption ? ` - ${content.caption}` : ''}`}
          className="w-full rounded-md object-contain"
          loading="lazy"
        />
      </a>
      {content.caption && (
        <p className="mt-2 text-sm text-[var(--color-text-muted)] italic">
          {content.caption}
        </p>
      )}
    </div>
  ) : null;

  const textElement = (
    <div className="flex-1 min-w-0">
      <div
        className="prose prose-stone max-w-none dark:prose-invert"
        dangerouslySetInnerHTML={{ __html: cleanHtml }}
      />
    </div>
  );

  return (
    <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
      {imageOnLeft ? (
        <>
          {imageElement}
          {textElement}
        </>
      ) : (
        <>
          {textElement}
          {imageElement}
        </>
      )}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Block: gallery                                                             */
/* -------------------------------------------------------------------------- */

interface GalleryItem {
  document_id: number;
  file_id?: number;
  caption?: string;
}

interface GalleryContent {
  items?: GalleryItem[];
  columns?: 2 | 3 | 4;
  show_captions?: boolean;
}

function GalleryBlock({ content }: { content: GalleryContent }) {
  const items = content.items ?? [];
  const docIds = items.map((item) => item.document_id);
  const { data, isLoading, isError } = usePublicDocuments(
    docIds.length > 0 ? docIds : undefined,
  );

  if (items.length === 0) {
    return (
      <p className="text-[var(--color-text-muted)] text-sm">
        No items in this gallery.
      </p>
    );
  }

  if (isLoading) {
    return <Spinner label="Loading gallery" />;
  }

  if (isError) {
    return <BlockError message="Unable to load gallery documents." />;
  }

  const documents = data?.items ?? [];
  const docMap = new Map(documents.map((d) => [d.id, d]));

  const columns = content.columns ?? 3;
  const gridCols: Record<number, string> = {
    2: 'grid-cols-1 sm:grid-cols-2',
    3: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3',
    4: 'grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4',
  };

  return (
    <div
      className={`grid gap-4 ${gridCols[columns] ?? gridCols[3]}`}
      role="list"
      aria-label="Document gallery"
    >
      {items.map((item, index) => {
        const doc = docMap.get(item.document_id);
        if (!doc) return null;

        const imgSrc = thumbnailUrl(doc, item.file_id);
        const caption = item.caption || doc.title;

        return (
          <div
            key={`${item.document_id}-${index}`}
            className="group overflow-hidden rounded-lg border border-[var(--color-border)] bg-white dark:bg-gray-800"
            role="listitem"
          >
            <a
              href={`/public/documents/${doc.id}`}
              className="block focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)]"
              aria-label={`View document: ${doc.title}`}
            >
              {imgSrc ? (
                <img
                  src={imgSrc}
                  alt={doc.title}
                  className="aspect-square w-full object-cover transition-transform group-hover:scale-105"
                  loading="lazy"
                />
              ) : (
                <div
                  className="flex aspect-square w-full items-center justify-center bg-gray-100 dark:bg-gray-700"
                  aria-hidden="true"
                >
                  <span className="text-3xl text-[var(--color-text-muted)]">
                    &#128196;
                  </span>
                </div>
              )}
            </a>
            {content.show_captions !== false && caption && (
              <div className="p-3">
                <p className="text-sm text-[var(--color-text-secondary)]">
                  {caption}
                </p>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Block: document_metadata                                                   */
/* -------------------------------------------------------------------------- */

interface DocumentMetadataContent {
  document_id?: number;
  show_citation?: boolean;
  show_download?: boolean;
  show_transcription?: boolean;
}

function DocumentMetadataBlock({
  content,
}: {
  content: DocumentMetadataContent;
}) {
  const { data: doc, isLoading, isError } = usePublicDocument(
    content.document_id,
  );

  if (isLoading) {
    return <Spinner label="Loading document details" />;
  }

  if (isError || !doc) {
    return <BlockError message="Unable to load document metadata." />;
  }

  const firstFile = doc.files?.[0];
  const imgSrc = firstFile ? thumbnailUrl(doc, firstFile.id) : null;
  const ocrText = firstFile?.ocr_text ?? null;

  /** Builds a list of metadata rows for public ISAD(G) fields that have values. */
  const metadataRows: Array<{ label: string; value: string }> = [];

  if (doc.accession_number) {
    metadataRows.push({ label: 'Accession Number', value: doc.accession_number });
  }
  if (doc.reference_code) {
    metadataRows.push({ label: 'Reference Code', value: doc.reference_code });
  }
  if (doc.date_display) {
    metadataRows.push({ label: 'Date', value: doc.date_display });
  }
  if (doc.creator?.authorized_name) {
    metadataRows.push({ label: 'Creator', value: doc.creator.authorized_name });
  }
  if (doc.extent) {
    metadataRows.push({ label: 'Extent', value: doc.extent });
  }
  if (doc.scope_and_content) {
    metadataRows.push({
      label: 'Scope and Content',
      value: doc.scope_and_content,
    });
  }
  if (doc.language_of_material) {
    metadataRows.push({ label: 'Language', value: doc.language_of_material });
  }
  if (doc.access_conditions) {
    metadataRows.push({
      label: 'Conditions of Access',
      value: doc.access_conditions,
    });
  }
  if (doc.copyright_status && doc.copyright_status !== 'unknown') {
    metadataRows.push({
      label: 'Copyright Status',
      value: doc.copyright_status.replace(/_/g, ' '),
    });
  }
  if (doc.rights_holder) {
    metadataRows.push({ label: 'Rights Holder', value: doc.rights_holder });
  }
  if (doc.rights_note) {
    metadataRows.push({ label: 'Rights', value: doc.rights_note });
  }
  if (doc.geo_location_name) {
    metadataRows.push({ label: 'Location', value: doc.geo_location_name });
  }

  return (
    <article
      className="overflow-hidden rounded-lg border border-[var(--color-border)] bg-white dark:bg-gray-800"
      aria-label={`Document: ${doc.title}`}
    >
      {/* Document viewer */}
      {imgSrc && (
        <div className="bg-gray-100 dark:bg-gray-900 p-4">
          <a
            href={`/public/documents/${doc.id}`}
            aria-label={`View full document: ${doc.title}`}
          >
            <img
              src={imgSrc}
              alt={
                ocrText
                  ? `Page 1 of ${doc.files?.[0]?.page_count ?? 1}. Transcript available below.`
                  : `Page 1 of ${doc.files?.[0]?.page_count ?? 1}.`
              }
              className="mx-auto max-h-[500px] object-contain"
            />
          </a>
        </div>
      )}

      {/* Content advisory */}
      {doc.has_content_advisory && (
        <div
          className="border-b border-[var(--color-warning)] bg-yellow-50 px-6 py-3 text-sm text-[var(--color-warning)] dark:bg-yellow-900/20"
          role="alert"
        >
          {doc.content_advisory_note ??
            'This item may contain language or content that reflects historical attitudes that are harmful or offensive to modern readers.'}
        </div>
      )}

      <div className="p-6">
        {/* Title */}
        <h3 className="text-xl font-semibold text-[var(--color-text-primary)] mb-4">
          <a
            href={`/public/documents/${doc.id}`}
            className="text-[var(--color-link)] underline hover:text-[var(--color-link-visited)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)]"
          >
            {doc.title}
          </a>
        </h3>

        {/* Metadata table */}
        {metadataRows.length > 0 && (
          <dl className="grid grid-cols-1 gap-3 sm:grid-cols-[auto_1fr]">
            {metadataRows.map((row) => (
              <div
                key={row.label}
                className="sm:contents"
              >
                <dt className="font-medium text-sm text-[var(--color-text-primary)]">
                  {row.label}
                </dt>
                <dd className="text-sm text-[var(--color-text-secondary)] mb-2 sm:mb-0">
                  {row.value}
                </dd>
              </div>
            ))}
          </dl>
        )}

        {/* Transcription */}
        {content.show_transcription && ocrText && (
          <details className="mt-4">
            <summary className="cursor-pointer text-sm font-medium text-[var(--color-link)] hover:text-[var(--color-link-visited)] min-h-[44px] flex items-center">
              View transcript
            </summary>
            <div className="mt-2 rounded-md bg-gray-50 p-4 text-sm whitespace-pre-wrap text-[var(--color-text-secondary)] dark:bg-gray-900">
              {ocrText}
            </div>
          </details>
        )}

        {/* Actions */}
        <div className="mt-4 flex flex-wrap gap-3">
          {content.show_citation && (
            <a
              href={`/public/documents/${doc.id}#citation`}
              className="inline-flex items-center rounded-md border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-text-primary)] hover:bg-gray-50 dark:hover:bg-gray-700 min-h-[44px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)]"
            >
              Cite this document
            </a>
          )}
          {content.show_download && firstFile && (
            <a
              href={`/api/v1/public/documents/${doc.id}/files/${firstFile.id}`}
              download
              className="inline-flex items-center rounded-md border border-[var(--color-border)] px-4 py-2 text-sm font-medium text-[var(--color-text-primary)] hover:bg-gray-50 dark:hover:bg-gray-700 min-h-[44px] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)]"
            >
              Download file
            </a>
          )}
        </div>
      </div>
    </article>
  );
}

/* -------------------------------------------------------------------------- */
/*  Block: map                                                                 */
/* -------------------------------------------------------------------------- */

interface MapContent {
  center_lat?: number;
  center_lon?: number;
  zoom?: number;
  document_ids?: number[];
  query?: Record<string, unknown>;
  show_popups?: boolean;
  basemap?: 'openstreetmap' | 'satellite';
}

/**
 * Error boundary that catches failures from lazy-loading MapBlock (e.g. if the
 * MapBlock module does not exist or Leaflet fails to initialize). Renders a
 * graceful fallback instead of crashing the entire exhibition page.
 */
class MapErrorBoundary extends Component<
  { children: ReactNode },
  { hasError: boolean }
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(): { hasError: boolean } {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // Log for debugging; MapBlock may not be implemented yet.
    console.error('MapBlock failed to load:', error, info);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div
          className="flex min-h-[300px] items-center justify-center rounded-lg border-2 border-dashed border-[var(--color-border)] bg-gray-50 dark:bg-gray-800"
          role="img"
          aria-label="Map: content not available"
        >
          <p className="text-[var(--color-text-muted)] text-sm">
            Interactive map is currently unavailable.
          </p>
        </div>
      );
    }
    return this.props.children;
  }
}

function MapBlockWrapper({ content }: { content: MapContent }) {
  return (
    <MapErrorBoundary>
      <Suspense fallback={<Spinner label="Loading map" />}>
        <LazyMapBlock
          centerLat={content.center_lat ?? 38.88}
          centerLon={content.center_lon ?? -77.17}
          zoom={content.zoom ?? 10}
          documentIds={content.document_ids}
          showPopups={content.show_popups ?? true}
          basemap={content.basemap ?? 'openstreetmap'}
        />
      </Suspense>
    </MapErrorBoundary>
  );
}

/* -------------------------------------------------------------------------- */
/*  Block: timeline                                                            */
/* -------------------------------------------------------------------------- */

interface TimelineContent {
  document_ids?: number[];
  query?: {
    term_ids?: number[];
    node_id?: number;
    date_from?: string;
    date_to?: string;
  };
  title_field?: string;
  date_field?: 'date_start' | 'date_display';
  show_descriptions?: boolean;
}

function TimelineBlockWrapper({ content }: { content: TimelineContent }) {
  return (
    <TimelineBlock
      documentIds={content.document_ids}
      query={content.query}
      titleField={content.title_field}
      dateField={content.date_field}
      showDescriptions={content.show_descriptions}
    />
  );
}

/* -------------------------------------------------------------------------- */
/*  Block: table_of_contents                                                   */
/* -------------------------------------------------------------------------- */

interface TocContent {
  depth?: 1 | 2 | 3;
}

function buildPageTree(
  pages: ExhibitionPage[],
  parentId: number | null,
  depth: number,
  currentDepth: number,
): ExhibitionPage[] {
  if (currentDepth > depth) return [];
  return pages
    .filter((p) => p.parent_page_id === parentId && p.is_public)
    .sort((a, b) => a.sort_order - b.sort_order);
}

function TocList({
  pages,
  allPages,
  depth,
  currentDepth,
  exhibitionSlug,
}: {
  pages: ExhibitionPage[];
  allPages: ExhibitionPage[];
  depth: number;
  currentDepth: number;
  exhibitionSlug: string;
}) {
  if (pages.length === 0) return null;

  return (
    <ul className={`${currentDepth === 1 ? '' : 'ml-6'} list-none`}>
      {pages.map((page) => {
        const children = buildPageTree(
          allPages,
          page.id,
          depth,
          currentDepth + 1,
        );

        return (
          <li key={page.id} className="my-1">
            <a
              href={`/public/exhibits/${exhibitionSlug}/${page.slug}`}
              className="text-[var(--color-link)] underline hover:text-[var(--color-link-visited)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)] inline-flex min-h-[44px] items-center"
            >
              {page.menu_title ?? page.title}
            </a>
            {children.length > 0 && currentDepth < depth && (
              <TocList
                pages={children}
                allPages={allPages}
                depth={depth}
                currentDepth={currentDepth + 1}
                exhibitionSlug={exhibitionSlug}
              />
            )}
          </li>
        );
      })}
    </ul>
  );
}

function TableOfContentsBlock({
  content,
  exhibitionSlug,
  pages,
}: {
  content: TocContent;
  exhibitionSlug: string;
  pages: ExhibitionPage[];
}) {
  const depth = content.depth ?? 2;

  if (!pages || pages.length === 0) {
    return (
      <p className="text-[var(--color-text-muted)] text-sm">
        No pages available.
      </p>
    );
  }

  const topLevelPages = buildPageTree(pages, null, depth, 1);

  return (
    <nav aria-label="Table of contents">
      <TocList
        pages={topLevelPages}
        allPages={pages}
        depth={depth}
        currentDepth={1}
        exhibitionSlug={exhibitionSlug}
      />
    </nav>
  );
}

/* -------------------------------------------------------------------------- */
/*  Block: collection_browse                                                   */
/* -------------------------------------------------------------------------- */

interface CollectionBrowseContent {
  node_id?: number;
  display?: 'grid' | 'list';
  per_page?: number;
  show_metadata?: boolean;
}

function CollectionBrowseBlock({
  content,
}: {
  content: CollectionBrowseContent;
}) {
  const perPage = content.per_page ?? 12;
  const { data, isLoading, isError } = useCollectionDocuments(
    content.node_id,
    perPage,
  );

  if (!content.node_id) {
    return <BlockError message="No collection specified for this block." />;
  }

  if (isLoading) {
    return <Spinner label="Loading collection" />;
  }

  if (isError) {
    return <BlockError message="Unable to load collection documents." />;
  }

  const documents = data?.items ?? [];
  const displayMode = content.display ?? 'grid';

  if (documents.length === 0) {
    return (
      <p className="text-[var(--color-text-muted)] text-sm">
        No public documents in this collection.
      </p>
    );
  }

  if (displayMode === 'list') {
    return (
      <div role="list" aria-label="Collection documents">
        {documents.map((doc) => (
          <div
            key={doc.id}
            className="flex items-start gap-4 border-b border-[var(--color-border)] py-4 last:border-b-0"
            role="listitem"
          >
            {doc.files?.[0]?.thumbnail_path && (
              <img
                src={thumbnailUrl(doc)!}
                alt=""
                className="h-16 w-16 flex-shrink-0 rounded object-cover"
                loading="lazy"
              />
            )}
            <div className="min-w-0 flex-1">
              <h4 className="text-sm font-semibold">
                <a
                  href={`/public/documents/${doc.id}`}
                  className="text-[var(--color-link)] underline hover:text-[var(--color-link-visited)] focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)]"
                >
                  {doc.title}
                </a>
              </h4>
              {content.show_metadata && (
                <p className="text-xs text-[var(--color-text-muted)] mt-1">
                  {[doc.date_display, doc.creator?.authorized_name]
                    .filter(Boolean)
                    .join(' \u2014 ')}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    );
  }

  // Grid display
  return (
    <div
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4"
      role="list"
      aria-label="Collection documents"
    >
      {documents.map((doc) => {
        const imgSrc = thumbnailUrl(doc);

        return (
          <div
            key={doc.id}
            className="group overflow-hidden rounded-lg border border-[var(--color-border)] bg-white dark:bg-gray-800"
            role="listitem"
          >
            <a
              href={`/public/documents/${doc.id}`}
              className="block focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--color-focus)]"
              aria-label={`View document: ${doc.title}`}
            >
              {imgSrc ? (
                <img
                  src={imgSrc}
                  alt={doc.title}
                  className="aspect-[4/3] w-full object-cover transition-transform group-hover:scale-105"
                  loading="lazy"
                />
              ) : (
                <div
                  className="flex aspect-[4/3] w-full items-center justify-center bg-gray-100 dark:bg-gray-700"
                  aria-hidden="true"
                >
                  <span className="text-3xl text-[var(--color-text-muted)]">
                    &#128196;
                  </span>
                </div>
              )}
            </a>
            <div className="p-3">
              <h4 className="text-sm font-semibold text-[var(--color-text-primary)] truncate">
                {doc.title}
              </h4>
              {content.show_metadata && (
                <p className="text-xs text-[var(--color-text-muted)] mt-1 truncate">
                  {[doc.date_display, doc.creator?.authorized_name]
                    .filter(Boolean)
                    .join(' \u2014 ')}
                </p>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

/* -------------------------------------------------------------------------- */
/*  Block: separator                                                           */
/* -------------------------------------------------------------------------- */

interface SeparatorContent {
  style?: 'solid' | 'dashed' | 'blank';
}

function SeparatorBlock({ content }: { content: SeparatorContent }) {
  const style = content.style ?? 'solid';

  if (style === 'blank') {
    return <div className="h-8" role="separator" aria-hidden="true" />;
  }

  const borderStyle = style === 'dashed' ? 'border-dashed' : 'border-solid';

  return (
    <hr
      className={`border-t border-[var(--color-border)] ${borderStyle} my-4`}
      role="separator"
    />
  );
}

/* -------------------------------------------------------------------------- */
/*  Main renderer                                                              */
/* -------------------------------------------------------------------------- */

export default function ExhibitionBlockRenderer({
  block,
  exhibitionSlug = '',
  pages = [],
}: ExhibitionBlockRendererProps) {
  const content = block.content;

  function renderBlock() {
    switch (block.block_type) {
      case 'html':
        return <HtmlBlock content={content as { html?: string }} />;

      case 'file_with_text':
        return (
          <FileWithTextBlock content={content as FileWithTextContent} />
        );

      case 'gallery':
        return <GalleryBlock content={content as GalleryContent} />;

      case 'document_metadata':
        return (
          <DocumentMetadataBlock
            content={content as DocumentMetadataContent}
          />
        );

      case 'map':
        return <MapBlockWrapper content={content as MapContent} />;

      case 'timeline':
        return <TimelineBlockWrapper content={content as TimelineContent} />;

      case 'table_of_contents':
        return (
          <TableOfContentsBlock
            content={content as TocContent}
            exhibitionSlug={exhibitionSlug}
            pages={pages}
          />
        );

      case 'collection_browse':
        return (
          <CollectionBrowseBlock
            content={content as CollectionBrowseContent}
          />
        );

      case 'separator':
        return <SeparatorBlock content={content as SeparatorContent} />;

      default:
        return (
          <BlockError
            message={`Unknown block type: "${block.block_type}".`}
          />
        );
    }
  }

  return <BlockLayout layout={block.layout}>{renderBlock()}</BlockLayout>;
}
