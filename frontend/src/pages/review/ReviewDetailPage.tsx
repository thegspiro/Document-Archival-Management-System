/**
 * Review detail page with side-by-side comparison of current values
 * and LLM/NER suggestions. Supports approve and reject actions.
 */
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../api/client';
import { documentsApi } from '../../api/documents';
import Spinner from '../../components/ui/Spinner';
import type { Document, ReviewQueueItem } from '../../types/api';

export default function ReviewDetailPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const docId = Number(documentId);

  const reviewQuery = useQuery<ReviewQueueItem>({
    queryKey: ['review', docId],
    queryFn: () => apiClient.get(`/review/${docId}`).then((r) => r.data),
    enabled: !Number.isNaN(docId),
  });

  const docQuery = useQuery<Document>({
    queryKey: ['documents', docId],
    queryFn: () => documentsApi.get(docId),
    enabled: !Number.isNaN(docId),
  });

  const approveMutation = useMutation({
    mutationFn: () => apiClient.post(`/review/${docId}/approve`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['review'] }); navigate('/review'); },
  });

  const rejectMutation = useMutation({
    mutationFn: () => apiClient.post(`/review/${docId}/reject`),
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ['review'] }); navigate('/review'); },
  });

  if (reviewQuery.isLoading || docQuery.isLoading) {
    return <div className="flex items-center justify-center py-16"><Spinner label="Loading review" /></div>;
  }

  const doc = docQuery.data;
  const review = reviewQuery.data;

  if (reviewQuery.isError || docQuery.isError || !doc) {
    return (
      <div className="p-6 max-w-5xl mx-auto">
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load review item.</div>
        <Link to="/review" className="mt-4 inline-block text-blue-700 dark:text-blue-400 hover:underline">Back to review queue</Link>
      </div>
    );
  }

  const suggestions = doc.llm_suggestions as Record<string, string> | null;
  const suggestionEntries = suggestions ? Object.entries(suggestions).filter(([, v]) => v != null && v !== '') : [];

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <nav aria-label="Breadcrumb" className="text-sm text-gray-500 dark:text-gray-400 mb-2">
        <Link to="/review" className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">Review Queue</Link>
        <span aria-hidden="true"> / </span>
        <span aria-current="page">{doc.accession_number ?? doc.title}</span>
      </nav>

      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">Review: {doc.title}</h1>

      {review && (
        <div className="mb-6 flex items-center gap-3 text-sm text-gray-600 dark:text-gray-400">
          <span>Reason: <span className="capitalize font-medium">{review.reason.replace(/_/g, ' ')}</span></span>
          <span>Priority: <span className="capitalize font-medium">{review.priority}</span></span>
        </div>
      )}

      <section aria-labelledby="suggestions-heading" className="mb-8">
        <h2 id="suggestions-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Suggested Changes</h2>
        {suggestionEntries.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">No suggestions available. Manual review required.</p>
        ) : (
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4">
            <div className="grid grid-cols-3 gap-4 pb-2 border-b border-gray-200 dark:border-gray-700 mb-2">
              <p className="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Field</p>
              <p className="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Current Value</p>
              <p className="text-xs font-semibold uppercase text-gray-500 dark:text-gray-400">Suggested Value</p>
            </div>
            {suggestionEntries.map(([field, suggested]) => (
              <div key={field} className="grid grid-cols-3 gap-4 py-3 border-b border-gray-100 dark:border-gray-700">
                <p className="text-sm font-medium text-gray-700 dark:text-gray-300 capitalize">{field.replace(/_/g, ' ')}</p>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {(doc as unknown as Record<string, string | null>)[field] || <span className="italic text-gray-400 dark:text-gray-500">empty</span>}
                </p>
                <p className="text-sm text-blue-700 dark:text-blue-400 font-medium">{String(suggested)}</p>
              </div>
            ))}
          </div>
        )}
      </section>

      <section aria-labelledby="doc-info-heading" className="mb-8">
        <h2 id="doc-info-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Document Information</h2>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 space-y-2 text-sm">
          <p><span className="font-medium text-gray-700 dark:text-gray-300">Title:</span> {doc.title}</p>
          <p><span className="font-medium text-gray-700 dark:text-gray-300">Accession:</span> {doc.accession_number ?? 'Not assigned'}</p>
          <p><span className="font-medium text-gray-700 dark:text-gray-300">Date:</span> {doc.date_display ?? 'Not set'}</p>
          <Link to={`/archive/documents/${doc.id}`}
            className="inline-block text-blue-700 dark:text-blue-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
            View full document record
          </Link>
        </div>
      </section>

      <div className="flex items-center gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
        <button type="button" onClick={() => approveMutation.mutate()} disabled={approveMutation.isPending || rejectMutation.isPending}
          className="min-h-[44px] px-6 py-2 rounded bg-green-700 hover:bg-green-800 text-white font-medium text-sm disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          {approveMutation.isPending ? 'Approving...' : 'Approve'}
        </button>
        <button type="button" onClick={() => rejectMutation.mutate()} disabled={approveMutation.isPending || rejectMutation.isPending}
          className="min-h-[44px] px-6 py-2 rounded bg-red-700 hover:bg-red-800 text-white font-medium text-sm disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          {rejectMutation.isPending ? 'Rejecting...' : 'Reject'}
        </button>
        <Link to={`/archive/documents/${doc.id}/edit`}
          className="min-h-[44px] inline-flex items-center px-4 py-2 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
          Edit Manually
        </Link>
        <Link to="/review" className="ml-auto min-h-[44px] inline-flex items-center px-4 py-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
          Back to Queue
        </Link>
      </div>
    </div>
  );
}
