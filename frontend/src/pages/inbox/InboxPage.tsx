/**
 * Inbox page listing unprocessed documents (inbox_status = 'inbox').
 * Supports multi-select for bulk clearing and quick navigation to detail.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import { documentsApi } from '../../api/documents';
import Spinner from '../../components/ui/Spinner';
import type { Document, PaginatedResponse } from '../../types/api';

export default function InboxPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const page = Number(searchParams.get('page') ?? '1');
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery<PaginatedResponse<Document>>({
    queryKey: ['documents', 'inbox', page],
    queryFn: () => documentsApi.list({ inbox_status: 'inbox', page, per_page: 25 }),
  });

  const bulkMutation = useMutation({
    mutationFn: () =>
      documentsApi.bulk({ document_ids: selectedIds, action: { type: 'clear_inbox' } }),
    onSuccess: () => {
      setSelectedIds([]);
      queryClient.invalidateQueries({ queryKey: ['documents', 'inbox'] });
    },
  });

  const toggleDoc = (id: number) => {
    setSelectedIds((prev) => prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id]);
  };

  const toggleAll = () => {
    if (!data) return;
    const allIds = data.items.map((d) => d.id);
    setSelectedIds(allIds.every((id) => selectedIds.includes(id)) ? [] : allIds);
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Inbox</h1>
        {selectedIds.length > 0 && (
          <div className="flex items-center gap-3">
            <span className="text-sm text-gray-600 dark:text-gray-400">{selectedIds.length} selected</span>
            <button type="button" onClick={() => bulkMutation.mutate()} disabled={bulkMutation.isPending}
              className="min-h-[44px] px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
              {bulkMutation.isPending ? 'Processing...' : 'Mark as Processed'}
            </button>
          </div>
        )}
      </div>

      {isLoading && <div className="flex items-center justify-center py-16"><Spinner label="Loading inbox" /></div>}

      {isError && (
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
          Failed to load inbox documents.
        </div>
      )}

      {data && data.items.length === 0 && (
        <div className="text-center py-16">
          <p className="text-gray-500 dark:text-gray-400 text-lg">Inbox is empty.</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">New documents from uploads and watch folders will appear here.</p>
        </div>
      )}

      {data && data.items.length > 0 && (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th scope="col" className="w-10 px-4 py-3">
                    <input type="checkbox" checked={data.items.length > 0 && data.items.every((d) => selectedIds.includes(d.id))}
                      onChange={toggleAll} aria-label="Select all documents on this page" className="h-4 w-4" />
                  </th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Title</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Accession</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Date Added</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {data.items.map((doc) => (
                  <tr key={doc.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3">
                      <input type="checkbox" checked={selectedIds.includes(doc.id)} onChange={() => toggleDoc(doc.id)}
                        aria-label={`Select document: ${doc.title}`} className="h-4 w-4" />
                    </td>
                    <td className="px-4 py-3">
                      <Link to={`/archive/documents/${doc.id}`}
                        className="text-blue-700 dark:text-blue-400 hover:underline font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                        {doc.title}
                      </Link>
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">{doc.accession_number ?? '\u2014'}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                      <time dateTime={doc.created_at}>{new Date(doc.created_at).toLocaleDateString()}</time>
                    </td>
                    <td className="px-4 py-3"><span className="text-xs capitalize text-gray-500 dark:text-gray-400">{doc.description_status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {data.pages > 1 && (
            <nav aria-label="Inbox pagination" className="mt-4 flex items-center justify-center gap-2">
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
