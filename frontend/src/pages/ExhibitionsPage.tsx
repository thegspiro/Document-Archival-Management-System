/**
 * Exhibitions management list. Shows all exhibitions with publish status.
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { exhibitionsApi } from '../api/exhibitions';
import Spinner from '../components/ui/Spinner';
import type { Exhibition, PaginatedResponse } from '../types/api';

export default function ExhibitionsPage() {
  const { data, isLoading, isError } = useQuery<PaginatedResponse<Exhibition>>({
    queryKey: ['exhibitions'],
    queryFn: () => exhibitionsApi.list({ per_page: 50 }),
  });

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Exhibitions</h1>
        <Link to="/exhibitions/new"
          className="min-h-[44px] inline-flex items-center px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          New Exhibition
        </Link>
      </div>

      {isLoading && <div className="flex items-center justify-center py-16"><Spinner label="Loading exhibitions" /></div>}
      {isError && <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load exhibitions.</div>}

      {data && data.items.length === 0 && (
        <div className="text-center py-16">
          <p className="text-gray-500 dark:text-gray-400 text-lg">No exhibitions yet.</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">Create your first exhibition to get started.</p>
        </div>
      )}

      {data && data.items.length > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.items.map((exhibition) => (
            <article key={exhibition.id}
              className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-md transition-shadow">
              {exhibition.cover_image_path && (
                <img src={exhibition.cover_image_path} alt="" className="w-full h-40 object-cover" />
              )}
              {!exhibition.cover_image_path && (
                <div className="w-full h-40 bg-gray-100 dark:bg-gray-700 flex items-center justify-center">
                  <span className="text-gray-400 dark:text-gray-500 text-sm">No cover image</span>
                </div>
              )}
              <div className="p-4">
                <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                  <Link to={`/exhibitions/${exhibition.id}/edit`}
                    className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                    {exhibition.title}
                  </Link>
                </h2>
                {exhibition.subtitle && <p className="text-sm text-gray-500 dark:text-gray-400 mb-2">{exhibition.subtitle}</p>}
                <div className="flex items-center gap-2">
                  {exhibition.is_published ? (
                    <span className="text-xs text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/30 rounded px-2 py-0.5">Published</span>
                  ) : (
                    <span className="text-xs text-gray-500 dark:text-gray-400 bg-gray-100 dark:bg-gray-700 rounded px-2 py-0.5">Draft</span>
                  )}
                  <span className="text-xs text-gray-400 dark:text-gray-500">/{exhibition.slug}</span>
                </div>
              </div>
            </article>
          ))}
        </div>
      )}
    </div>
  );
}
