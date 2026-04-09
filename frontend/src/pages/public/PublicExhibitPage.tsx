/**
 * Public exhibition page with rendered content blocks.
 * Supports exhibition summary and individual page views.
 * Embeds Schema.org ExhibitionEvent JSON-LD structured data.
 */
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import { generateExhibitionLD } from '../../utils/structuredData';
import { useInstitution } from '../../context/InstitutionContext';
import type { Exhibition, ExhibitionPage, ExhibitionPageBlock } from '../../types/api';

function RenderBlock({ block }: { block: ExhibitionPageBlock }) {
  const content = block.content as Record<string, unknown>;

  switch (block.block_type) {
    case 'html':
      return (
        <div className="prose dark:prose-invert max-w-none"
          dangerouslySetInnerHTML={{ __html: (content.html as string) ?? '' }} />
      );
    case 'file_with_text':
      return (
        <div className={`flex gap-6 ${(content.image_position as string) === 'right' ? 'flex-row-reverse' : 'flex-row'}`}>
          <div className="w-1/2 bg-gray-100 dark:bg-gray-700 rounded-lg p-4 flex items-center justify-center">
            <p className="text-sm text-gray-500 dark:text-gray-400">Document #{content.document_id as number}</p>
          </div>
          <div className="w-1/2 prose dark:prose-invert max-w-none"
            dangerouslySetInnerHTML={{ __html: (content.text_html as string) ?? '' }} />
        </div>
      );
    case 'gallery':
      return (
        <div className={`grid grid-cols-${(content.columns as number) ?? 3} gap-4`}>
          {((content.items as Array<{ document_id: number; caption?: string }>) ?? []).map((item, i) => (
            <div key={i} className="bg-gray-100 dark:bg-gray-700 rounded-lg p-4 text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400">Document #{item.document_id}</p>
              {item.caption && <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{item.caption}</p>}
            </div>
          ))}
        </div>
      );
    case 'separator':
      return <hr className="my-8 border-gray-200 dark:border-gray-700" />;
    default:
      return (
        <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          <p className="text-sm text-gray-500 dark:text-gray-400">Content block: {block.block_type}</p>
        </div>
      );
  }
}

export default function PublicExhibitPage() {
  const { slug, pageSlug } = useParams<{ slug: string; pageSlug?: string }>();
  const institution = useInstitution();

  const exhibitQuery = useQuery<Exhibition>({
    queryKey: ['public', 'exhibitions', slug],
    queryFn: () => apiClient.get(`/public/exhibitions/${slug}`).then((r) => r.data),
    enabled: !!slug,
  });

  const pageQuery = useQuery<ExhibitionPage & { blocks: ExhibitionPageBlock[] }>({
    queryKey: ['public', 'exhibitions', slug, 'pages', pageSlug],
    queryFn: () => apiClient.get(`/public/exhibitions/${slug}/pages/${pageSlug}`).then((r) => r.data),
    enabled: !!slug && !!pageSlug,
  });

  if (exhibitQuery.isLoading) return <div className="flex justify-center py-16"><Spinner label="Loading exhibition" /></div>;

  if (exhibitQuery.isError || !exhibitQuery.data) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Exhibition not found.</div>
        <Link to="/public/exhibits" className="mt-4 inline-block text-blue-700 dark:text-blue-400 hover:underline">Back to exhibitions</Link>
      </div>
    );
  }

  const exhibition = exhibitQuery.data;
  const pages = exhibition.pages ?? [];

  // If no pageSlug, show summary or redirect info
  if (!pageSlug) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <nav aria-label="Breadcrumb" className="text-sm text-gray-500 dark:text-gray-400 mb-4">
          <Link to="/public/exhibits" className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">Exhibitions</Link>
          <span aria-hidden="true"> / </span>
          <span aria-current="page">{exhibition.title}</span>
        </nav>
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">{exhibition.title}</h1>
        {exhibition.subtitle && <p className="text-xl text-gray-600 dark:text-gray-400 mb-4">{exhibition.subtitle}</p>}
        {exhibition.description && <div className="prose dark:prose-invert max-w-none mb-8"><p>{exhibition.description}</p></div>}

        {pages.length > 0 && (
          <nav aria-label="Exhibition pages" className="mt-8">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Pages</h2>
            <ul className="space-y-2">
              {pages.map((page) => (
                <li key={page.id}>
                  <Link to={`/public/exhibits/${slug}/${page.slug}`}
                    className="block px-4 py-3 rounded bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 text-blue-700 dark:text-blue-400 hover:underline font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]">
                    {page.menu_title ?? page.title}
                  </Link>
                </li>
              ))}
            </ul>
          </nav>
        )}

        {/* Schema.org ExhibitionEvent structured data */}
        <script type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(
          generateExhibitionLD(exhibition, institution.name)
        ) }} />
      </div>
    );
  }

  // Specific page view
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <nav aria-label="Breadcrumb" className="text-sm text-gray-500 dark:text-gray-400 mb-4">
        <Link to="/public/exhibits" className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">Exhibitions</Link>
        <span aria-hidden="true"> / </span>
        <Link to={`/public/exhibits/${slug}`} className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">{exhibition.title}</Link>
        <span aria-hidden="true"> / </span>
        <span aria-current="page">{pageQuery.data?.title ?? pageSlug}</span>
      </nav>

      {pageQuery.isLoading && <div className="flex justify-center py-16"><Spinner label="Loading page" /></div>}
      {pageQuery.isError && <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load page.</div>}

      {pageQuery.data && (
        <>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">{pageQuery.data.title}</h1>
          <div className="space-y-8">
            {(pageQuery.data.blocks ?? []).map((block) => (
              <RenderBlock key={block.id} block={block} />
            ))}
          </div>
        </>
      )}

      {/* Page navigation */}
      {pages.length > 1 && (
        <nav aria-label="Exhibition page navigation" className="mt-12 pt-6 border-t border-gray-200 dark:border-gray-700 flex justify-between">
          {(() => {
            const currentIdx = pages.findIndex((p) => p.slug === pageSlug);
            const prev = currentIdx > 0 ? pages[currentIdx - 1] : null;
            const next = currentIdx < pages.length - 1 ? pages[currentIdx + 1] : null;
            return (
              <>
                {prev ? (
                  <Link to={`/public/exhibits/${slug}/${prev.slug}`}
                    className="text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                    &larr; {prev.menu_title ?? prev.title}
                  </Link>
                ) : <span />}
                {next ? (
                  <Link to={`/public/exhibits/${slug}/${next.slug}`}
                    className="text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                    {next.menu_title ?? next.title} &rarr;
                  </Link>
                ) : <span />}
              </>
            );
          })()}
        </nav>
      )}
    </div>
  );
}
