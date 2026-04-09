/**
 * Public collections browse page. Shows public arrangement nodes
 * with Schema.org Collection JSON-LD structured data.
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import { generateCollectionLD } from '../../utils/structuredData';
import { useInstitution } from '../../context/InstitutionContext';
import type { ArrangementNode } from '../../types/api';

export default function PublicCollectionsPage() {
  const institution = useInstitution();

  const { data, isLoading, isError } = useQuery<ArrangementNode[]>({
    queryKey: ['public', 'collections'],
    queryFn: () => apiClient.get('/public/collections').then((r) => r.data),
  });

  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-6">Collections</h1>

      {isLoading && <div className="flex justify-center py-16"><Spinner label="Loading collections" /></div>}
      {isError && <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load collections.</div>}

      {data && Array.isArray(data) && data.length === 0 && (
        <p className="text-gray-500 dark:text-gray-400 text-center py-16">No public collections available at this time.</p>
      )}

      {data && Array.isArray(data) && data.length > 0 && (
        <>
          <div className="space-y-4">
            {data.map((node) => (
              <article key={node.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                      <Link to={`/public/collections/${node.id}`}
                        className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                        {node.title}
                      </Link>
                    </h2>
                    <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400 mb-2">
                      <span className="capitalize">{node.level_type}</span>
                      {node.identifier && <span>{node.identifier}</span>}
                      {node.date_start && node.date_end && <span>{node.date_start} &ndash; {node.date_end}</span>}
                      {node.date_start && !node.date_end && <span>{node.date_start}</span>}
                    </div>
                    {node.description && (
                      <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">{node.description}</p>
                    )}
                  </div>
                </div>
              </article>
            ))}
          </div>

          {/* Schema.org Collection structured data for each public collection */}
          {data.map((node) => (
            <script key={`ld-${node.id}`} type="application/ld+json" dangerouslySetInnerHTML={{ __html: JSON.stringify(
              generateCollectionLD(node, institution.name)
            ) }} />
          ))}
        </>
      )}
    </div>
  );
}
