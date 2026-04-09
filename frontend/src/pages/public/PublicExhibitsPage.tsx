/**
 * Browse all published exhibitions. Filterable by tag.
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import type { Exhibition } from '../../types/api';

export default function PublicExhibitsPage() {
  const { data, isLoading, isError } = useQuery<{ items: Exhibition[] }>({
    queryKey: ['public', 'exhibitions', 'all'],
    queryFn: () => apiClient.get('/public/exhibitions').then((r) => r.data),
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-8">Exhibitions</h1>

      {isLoading && <div className="flex justify-center py-16"><Spinner label="Loading exhibitions" /></div>}
      {isError && <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load exhibitions.</div>}

      {data && data.items.length === 0 && (
        <p className="text-gray-500 dark:text-gray-400 text-center py-16">No published exhibitions at this time. Check back later.</p>
      )}

      {data && data.items.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.items.map((exhibition) => (
            <article key={exhibition.id}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
              {exhibition.cover_image_path ? (
                <img src={exhibition.cover_image_path} alt="" className="w-full h-48 object-cover" />
              ) : (
                <div className="w-full h-48 bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                  <span className="text-gray-400 dark:text-gray-500 text-sm">No cover image</span>
                </div>
              )}
              <div className="p-4">
                <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                  <Link to={`/public/exhibits/${exhibition.slug}`}
                    className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                    {exhibition.title}
                  </Link>
                </h2>
                {exhibition.subtitle && <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{exhibition.subtitle}</p>}
                {exhibition.description && (
                  <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">{exhibition.description}</p>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
