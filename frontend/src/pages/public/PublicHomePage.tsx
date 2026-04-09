/**
 * Public landing page. Shows institution name, published exhibitions grid,
 * and featured documents.
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import type { Exhibition } from '../../types/api';

export default function PublicHomePage() {
  const exhibitionsQuery = useQuery<{ items: Exhibition[] }>({
    queryKey: ['public', 'exhibitions'],
    queryFn: () => apiClient.get('/public/exhibitions').then((r) => r.data),
  });

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <header className="text-center mb-12">
        <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100 mb-2">Archival Document Management System</h1>
        <p className="text-lg text-gray-600 dark:text-gray-400">Explore our digital collections and exhibitions</p>
      </header>

      <nav className="flex justify-center gap-4 mb-12" aria-label="Public site navigation">
        <Link to="/public/exhibits"
          className="min-h-[44px] inline-flex items-center px-5 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          Browse Exhibitions
        </Link>
        <Link to="/public/collections"
          className="min-h-[44px] inline-flex items-center px-5 py-2 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium text-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          Browse Collections
        </Link>
        <Link to="/public/search"
          className="min-h-[44px] inline-flex items-center px-5 py-2 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 font-medium text-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          Search Documents
        </Link>
      </nav>

      <section aria-labelledby="exhibitions-heading">
        <h2 id="exhibitions-heading" className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Published Exhibitions</h2>
        {exhibitionsQuery.isLoading && <div className="flex justify-center py-8"><Spinner label="Loading exhibitions" /></div>}
        {exhibitionsQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load exhibitions.</p>}
        {exhibitionsQuery.data && exhibitionsQuery.data.items.length === 0 && (
          <p className="text-gray-500 dark:text-gray-400 text-center py-8">No published exhibitions at this time.</p>
        )}
        {exhibitionsQuery.data && exhibitionsQuery.data.items.length > 0 && (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {exhibitionsQuery.data.items.map((exhibition) => (
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
                  <h3 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                    <Link to={`/public/exhibits/${exhibition.slug}`}
                      className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                      {exhibition.title}
                    </Link>
                  </h3>
                  {exhibition.description && (
                    <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-3">{exhibition.description}</p>
                  )}
                </div>
              </article>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
