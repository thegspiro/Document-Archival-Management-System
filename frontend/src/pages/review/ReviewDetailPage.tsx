/**
 * Side-by-side review view: current values on left, LLM/NER suggestions on right
 * with accept/edit/reject per field.
 */
import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiClient from '../../api/client';
import { documentsApi } from '../../api/documents';
import type { Document } from '../../types/api';

interface SuggestionField {
  field: string;
  current_value: string | null;
  suggested_value: string;
  confidence: number | null;
}

type FieldDecision = 'pending' | 'accepted' | 'rejected' | 'edited';

function SuggestionRow({
  suggestion,
  decision,
  editedValue,
  onAccept,
  onReject,
  onEdit,
  onEditChange,
}: {
  suggestion: SuggestionField;
  decision: FieldDecision;
  editedValue: string;
  onAccept: () => void;
  onReject: () => void;
  onEdit: () => void;
  onEditChange: (val: string) => void;
}) {
  const fieldLabel = suggestion.field.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

  return (
    <div className="grid grid-cols-1 md:grid-cols-12 gap-4 py-4 border-b border-gray-100 dark:border-gray-700 last:border-b-0">
      <div className="md:col-span-2">
        <p className="text-sm font-medium text-gray-900 dark:text-gray-100">{fieldLabel}</p>
        {suggestion.confidence != null && (
          <p className="text-xs text-gray-400 dark:text-gray-500 mt-0.5">
            Confidence: {Math.round(suggestion.confidence * 100)}%
          </p>
        )}
      </div>

      <div className="md:col-span-4">
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Current</p>
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded px-3 py-2 text-sm text-gray-800 dark:text-gray-200 min-h-[40px]">
          {suggestion.current_value ?? <span className="italic text-gray-400">(empty)</span>}
        </div>
      </div>

      <div className="md:col-span-4">
        <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">Suggested</p>
        {decision === 'edited' ? (
          <textarea
            value={editedValue}
            onChange={(e) => onEditChange(e.target.value)}
            rows={2}
            className="w-full rounded border border-blue-300 dark:border-blue-600 bg-white dark:bg-gray-700 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
            aria-label={`Edit suggested value for ${fieldLabel}`}
          />
        ) : (
          <div
            className={`rounded px-3 py-2 text-sm min-h-[40px] ${
              decision === 'accepted'
                ? 'bg-green-50 dark:bg-green-900/30 text-green-800 dark:text-green-200 border border-green-200 dark:border-green-800'
                : decision === 'rejected'
                  ? 'bg-red-50 dark:bg-red-900/30 text-red-800 dark:text-red-200 line-through border border-red-200 dark:border-red-800'
                  : 'bg-blue-50 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 border border-blue-200 dark:border-blue-800'
            }`}
          >
            {suggestion.suggested_value}
          </div>
        )}
      </div>

      <div className="md:col-span-2 flex items-center gap-1">
        <button
          type="button"
          onClick={onAccept}
          disabled={decision === 'accepted'}
          className="min-h-[44px] min-w-[44px] px-2 py-1 rounded text-xs font-medium bg-green-600 text-white hover:bg-green-700 disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
          aria-label={`Accept suggestion for ${fieldLabel}`}
        >
          Accept
        </button>
        <button
          type="button"
          onClick={onEdit}
          disabled={decision === 'edited'}
          className="min-h-[44px] min-w-[44px] px-2 py-1 rounded text-xs font-medium bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
          aria-label={`Edit suggestion for ${fieldLabel}`}
        >
          Edit
        </button>
        <button
          type="button"
          onClick={onReject}
          disabled={decision === 'rejected'}
          className="min-h-[44px] min-w-[44px] px-2 py-1 rounded text-xs font-medium bg-red-600 text-white hover:bg-red-700 disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
          aria-label={`Reject suggestion for ${fieldLabel}`}
        >
          Reject
        </button>
      </div>
    </div>
  );
}

export default function ReviewDetailPage() {
  const { documentId } = useParams<{ documentId: string }>();
  const docId = Number(documentId);
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const [decisions, setDecisions] = useState<Record<string, FieldDecision>>({});
  const [editedValues, setEditedValues] = useState<Record<string, string>>({});

  const docQuery = useQuery<Document>({
    queryKey: ['document', docId],
    queryFn: () => documentsApi.get(docId),
    enabled: !isNaN(docId),
  });

  const suggestions: SuggestionField[] = docQuery.data?.llm_suggestions
    ? Object.entries(docQuery.data.llm_suggestions as Record<string, { value: string; confidence?: number }>)
        .filter(([, val]) => val && typeof val === 'object' && 'value' in val)
        .map(([field, val]) => ({
          field,
          current_value: (docQuery.data as unknown as Record<string, string | null>)[field] ?? null,
          suggested_value: val.value,
          confidence: val.confidence ?? null,
        }))
    : [];

  const approveMutation = useMutation({
    mutationFn: async () => {
      const updates: Record<string, string> = {};
      suggestions.forEach((s) => {
        const dec = decisions[s.field];
        if (dec === 'accepted') {
          updates[s.field] = s.suggested_value;
        } else if (dec === 'edited') {
          updates[s.field] = editedValues[s.field] ?? s.suggested_value;
        }
      });
      if (Object.keys(updates).length > 0) {
        await documentsApi.update(docId, updates);
      }
      await apiClient.post(`/review/${docId}/approve`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      queryClient.invalidateQueries({ queryKey: ['document', docId] });
      navigate('/review');
    },
  });

  const rejectMutation = useMutation({
    mutationFn: () => apiClient.post(`/review/${docId}/reject`).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      navigate('/review');
    },
  });

  const setDecision = (field: string, dec: FieldDecision) => {
    setDecisions((prev) => ({ ...prev, [field]: dec }));
  };

  if (docQuery.isLoading) {
    return (
      <div role="status" aria-label="Loading review" className="flex items-center justify-center py-20">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent" aria-hidden="true" />
        <span className="ml-3 text-gray-500 dark:text-gray-400">Loading document for review...</span>
      </div>
    );
  }

  if (docQuery.isError || !docQuery.data) {
    return (
      <div role="alert" className="p-6 max-w-3xl mx-auto">
        <div className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
          Document not found or failed to load.
        </div>
      </div>
    );
  }

  const doc = docQuery.data;

  return (
    <div className="max-w-6xl mx-auto p-6">
      <nav className="mb-4" aria-label="Breadcrumb">
        <Link to="/review" className="text-sm text-blue-600 dark:text-blue-400 hover:underline">
          &larr; Back to Review Queue
        </Link>
      </nav>

      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-1">Review: {doc.title}</h1>
      <p className="text-sm text-gray-500 dark:text-gray-400 mb-6">
        {doc.accession_number && <span>Accession: {doc.accession_number} &middot; </span>}
        Review status: {doc.review_status}
      </p>

      {suggestions.length === 0 ? (
        <div className="bg-gray-50 dark:bg-gray-700/50 rounded-lg p-8 text-center">
          <p className="text-gray-500 dark:text-gray-400">No LLM suggestions available for this document.</p>
          <div className="mt-4 flex items-center justify-center gap-3">
            <button type="button" onClick={() => approveMutation.mutate()} className="min-h-[44px] px-4 py-2 rounded bg-green-600 text-white hover:bg-green-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]">
              Approve
            </button>
            <button type="button" onClick={() => rejectMutation.mutate()} className="min-h-[44px] px-4 py-2 rounded bg-red-600 text-white hover:bg-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]">
              Reject
            </button>
          </div>
        </div>
      ) : (
        <>
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Suggested Changes</h2>
            {suggestions.map((s) => (
              <SuggestionRow
                key={s.field}
                suggestion={s}
                decision={decisions[s.field] ?? 'pending'}
                editedValue={editedValues[s.field] ?? s.suggested_value}
                onAccept={() => setDecision(s.field, 'accepted')}
                onReject={() => setDecision(s.field, 'rejected')}
                onEdit={() => {
                  setDecision(s.field, 'edited');
                  setEditedValues((prev) => ({ ...prev, [s.field]: prev[s.field] ?? s.suggested_value }));
                }}
                onEditChange={(val) => setEditedValues((prev) => ({ ...prev, [s.field]: val }))}
              />
            ))}
          </div>

          {(approveMutation.isError || rejectMutation.isError) && (
            <div role="alert" className="mt-4 p-3 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 text-sm">
              Action failed. Please try again.
            </div>
          )}

          <div className="mt-6 flex items-center gap-3">
            <button type="button" onClick={() => approveMutation.mutate()} disabled={approveMutation.isPending} className="min-h-[44px] px-6 py-2 rounded bg-green-600 text-white font-medium hover:bg-green-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2 disabled:opacity-60">
              {approveMutation.isPending ? 'Submitting...' : 'Submit Review'}
            </button>
            <button type="button" onClick={() => rejectMutation.mutate()} disabled={rejectMutation.isPending} className="min-h-[44px] px-6 py-2 rounded bg-red-600 text-white font-medium hover:bg-red-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2 disabled:opacity-60">
              Reject All
            </button>
            <button type="button" onClick={() => navigate('/review')} className="min-h-[44px] px-6 py-2 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
              Back to Queue
            </button>
          </div>
        </>
      )}
    </div>
  );
}
