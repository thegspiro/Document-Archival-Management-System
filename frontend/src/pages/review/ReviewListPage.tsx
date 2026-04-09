/**
 * Review queue list page. Shows documents pending review with
 * priority indicators and assignment information.
 */
import { useQuery } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import type { ReviewQueueItem, PaginatedResponse } from '../../types/api';

function PriorityBadge({ priority }: { priority: string }) {
  const styles: Record<string, string> = {
    low: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
    normal: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
    high: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300',
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium capitalize ${styles[priority] ?? styles.normal}`}
      role="img" aria-label={`Priority: ${priority}`}>{priority}</span>
  );
}

export default function ReviewListPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get('page') ?? '1');

  const { data, isLoading, isError } = useQuery<PaginatedResponse<ReviewQueueItem>>({
    queryKey: ['review', page],
    queryFn: () => apiClient.get('/review', { params: { page, per_page: 25 } }).then((r) => r.data),
  });

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Review Queue</h1>

      {isLoading && <div className="flex items-center justify-center py-16"><Spinner label="Loading review queue" /></div>}

      {isError && (
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
          Failed to load the review queue.
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className="text-center py-16">
          <p className="text-gray-500 dark:text-gray-400 text-lg">No items pending review.</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">Documents flagged for review will appear here.</p>
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Document</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Reason</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Priority</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Submitted</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium"><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {data.items.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      <p className="font-medium text-gray-900 dark:text-gray-100">{item.document?.title ?? `Document #${item.document_id}`}</p>
                      {item.document?.accession_number && <p className="text-xs text-gray-500 dark:text-gray-400">{item.document.accession_number}</p>}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400 capitalize text-xs">{item.reason.replace(/_/g, ' ')}</td>
                    <td className="px-4 py-3"><PriorityBadge priority={item.priority} /></td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      <time dateTime={item.created_at}>{new Date(item.created_at).toLocaleDateString()}</time>
                    </td>
                    <td className="px-4 py-3">
                      <Link to={`/review/${item.document_id}`}
                        className="min-h-[44px] inline-flex items-center px-3 py-1 rounded bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
                        Review
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data.pages > 1 && (
            <nav aria-label="Review queue pagination" className="mt-4 flex items-center justify-center gap-2">
              <button type="button" disabled={page <= 1} onClick={() => setSearchParams({ page: String(page - 1) })}
                className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
                aria-label="Previous page">Previous</button>
              <span className="text-sm text-gray-600 dark:text-gray-400" aria-current="page">Page {data.page} of {data.pages}</span>
              <button type="button" disabled={page >= data.pages} onClick={() => setSearchParams({ page: String(page + 1) })}
                className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
                aria-label="Next page">Next</button>
            </nav>
          )}
        </>
      )}
    </div>
  );
}
