/**
 * Archive browse page with sidebar tree navigation of arrangement_nodes.
 * Main panel shows documents in the selected node. Supports multi-select
 * with a bulk action toolbar at the bottom.
 */
import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link, useSearchParams } from 'react-router-dom';
import apiClient from '../../api/client';
import { documentsApi } from '../../api/documents';
import type { ArrangementNode, Document, PaginatedResponse } from '../../types/api';

/* ---------- Tree Node Component ---------- */

function TreeNode({
  node,
  selectedId,
  onSelect,
  level = 0,
}: {
  node: ArrangementNode;
  selectedId: number | null;
  onSelect: (id: number) => void;
  level?: number;
}) {
  const [expanded, setExpanded] = useState(level < 2);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <li role="treeitem" aria-expanded={hasChildren ? expanded : undefined} aria-level={level + 1}>
      <div
        className={`flex items-center py-1 px-2 rounded text-sm cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700 ${
          selectedId === node.id ? 'bg-blue-50 dark:bg-blue-900/30 font-medium' : ''
        }`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
      >
        {hasChildren && (
          <button
            type="button"
            onClick={(e) => {
              e.stopPropagation();
              setExpanded(!expanded);
            }}
            className="mr-1 w-5 h-5 flex items-center justify-center text-gray-400 hover:text-gray-600 dark:hover:text-gray-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded"
            aria-label={expanded ? `Collapse ${node.title}` : `Expand ${node.title}`}
          >
            {expanded ? '\u25BE' : '\u25B8'}
          </button>
        )}
        {!hasChildren && <span className="w-5 mr-1" aria-hidden="true" />}
        <button
          type="button"
          onClick={() => onSelect(node.id)}
          className="flex-1 text-left text-gray-900 dark:text-gray-100 truncate focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded px-1"
        >
          {node.title}
        </button>
        <span className="text-xs text-gray-400 dark:text-gray-500 ml-1 capitalize">
          {node.level_type}
        </span>
      </div>
      {hasChildren && expanded && (
        <ul role="group">
          {node.children!.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              selectedId={selectedId}
              onSelect={onSelect}
              level={level + 1}
            />
          ))}
        </ul>
      )}
    </li>
  );
}

/* ---------- Completeness Badge ---------- */

function CompletenessBadge({ level }: { level: string }) {
  const styles: Record<string, string> = {
    none: 'bg-gray-200 dark:bg-gray-600 text-gray-700 dark:text-gray-300',
    minimal: 'bg-amber-100 dark:bg-amber-900/40 text-amber-800 dark:text-amber-200',
    standard: 'bg-blue-100 dark:bg-blue-900/40 text-blue-800 dark:text-blue-200',
    full: 'bg-green-100 dark:bg-green-900/40 text-green-800 dark:text-green-200',
  };
  return (
    <span
      className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${styles[level] ?? styles.none}`}
      role="img"
      aria-label={`Description completeness: ${level}`}
    >
      {level}
    </span>
  );
}

/* ---------- Bulk Action Toolbar ---------- */

function BulkToolbar({
  selectedIds,
  onClear,
  onAction,
}: {
  selectedIds: number[];
  onClear: () => void;
  onAction: (action: string) => void;
}) {
  if (selectedIds.length === 0) return null;

  return (
    <div
      className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 shadow-lg px-6 py-3 flex items-center gap-4 z-40"
      role="toolbar"
      aria-label="Bulk actions"
    >
      <span className="text-sm font-medium text-gray-900 dark:text-gray-100">
        {selectedIds.length} selected
      </span>
      <button
        type="button"
        onClick={() => onAction('clear_inbox')}
        className="min-h-[44px] px-3 py-1 text-sm rounded bg-blue-600 text-white hover:bg-blue-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
      >
        Clear Inbox
      </button>
      <button
        type="button"
        onClick={() => onAction('set_public')}
        className="min-h-[44px] px-3 py-1 text-sm rounded bg-green-600 text-white hover:bg-green-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
      >
        Set Public
      </button>
      <button
        type="button"
        onClick={() => onAction('add_to_review')}
        className="min-h-[44px] px-3 py-1 text-sm rounded bg-purple-600 text-white hover:bg-purple-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
      >
        Add to Review
      </button>
      <button
        type="button"
        onClick={() => onAction('export_zip')}
        className="min-h-[44px] px-3 py-1 text-sm rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
      >
        Export ZIP
      </button>
      <div className="ml-auto">
        <button
          type="button"
          onClick={onClear}
          className="min-h-[44px] px-3 py-1 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
        >
          Clear selection
        </button>
      </div>
    </div>
  );
}

/* ---------- Main Page ---------- */

export default function ArchivePage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const selectedNodeId = searchParams.get('node') ? Number(searchParams.get('node')) : null;
  const page = Number(searchParams.get('page') ?? '1');
  const [selectedDocs, setSelectedDocs] = useState<number[]>([]);
  const queryClient = useQueryClient();

  const nodesQuery = useQuery<ArrangementNode[]>({
    queryKey: ['nodes', 'tree'],
    queryFn: () => apiClient.get('/nodes', { params: { tree: true } }).then((r) => r.data),
  });

  const docsQuery = useQuery<PaginatedResponse<Document>>({
    queryKey: ['documents', 'archive', selectedNodeId, page],
    queryFn: () =>
      documentsApi.list({
        ...(selectedNodeId ? { node_id: selectedNodeId } : {}),
        page,
        per_page: 25,
      }),
  });

  const bulkMutation = useMutation({
    mutationFn: (action: { type: string; [key: string]: unknown }) =>
      documentsApi.bulk({ document_ids: selectedDocs, action }),
    onSuccess: () => {
      setSelectedDocs([]);
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleNodeSelect = useCallback(
    (id: number) => {
      setSearchParams({ node: String(id) });
      setSelectedDocs([]);
    },
    [setSearchParams],
  );

  const toggleDoc = (id: number) => {
    setSelectedDocs((prev) =>
      prev.includes(id) ? prev.filter((d) => d !== id) : [...prev, id],
    );
  };

  const toggleAll = () => {
    if (!docsQuery.data) return;
    const allIds = docsQuery.data.items.map((d) => d.id);
    const allSelected = allIds.every((id) => selectedDocs.includes(id));
    setSelectedDocs(allSelected ? [] : allIds);
  };

  const handleBulkAction = (action: string) => {
    const actionPayload: Record<string, unknown> = { type: action };
    if (action === 'set_public') actionPayload.is_public = true;
    bulkMutation.mutate(actionPayload);
  };

  const docs = docsQuery.data;

  return (
    <div className="flex h-full">
      {/* Sidebar Tree */}
      <aside
        className="w-72 min-w-[288px] border-r border-gray-200 dark:border-gray-700 overflow-y-auto bg-white dark:bg-gray-800 p-3"
        aria-label="Collection hierarchy"
      >
        <h2 className="text-sm font-semibold text-gray-900 dark:text-gray-100 mb-2 px-2">
          Collections
        </h2>
        {nodesQuery.isLoading && (
          <p className="text-sm text-gray-500 dark:text-gray-400 px-2">Loading...</p>
        )}
        {nodesQuery.isError && (
          <p className="text-sm text-red-600 dark:text-red-400 px-2">Failed to load collections.</p>
        )}
        {nodesQuery.data && (
          <ul role="tree" aria-label="Arrangement hierarchy">
            {nodesQuery.data.map((node) => (
              <TreeNode
                key={node.id}
                node={node}
                selectedId={selectedNodeId}
                onSelect={handleNodeSelect}
              />
            ))}
          </ul>
        )}
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-y-auto p-6" id="main-content">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Archive</h1>
          <Link
            to="/archive/documents/new"
            className="min-h-[44px] inline-flex items-center px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2"
          >
            New Document
          </Link>
        </div>

        {docsQuery.isLoading && (
          <div role="status" aria-label="Loading documents" className="text-center py-12">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent" aria-hidden="true" />
            <p className="mt-2 text-gray-500 dark:text-gray-400">Loading documents...</p>
          </div>
        )}

        {docsQuery.isError && (
          <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
            Failed to load documents.
          </div>
        )}

        {docs && (
          <>
            {docs.items.length === 0 ? (
              <p className="text-gray-500 dark:text-gray-400 py-8 text-center">
                {selectedNodeId
                  ? 'No documents in this collection.'
                  : 'Select a collection to browse documents.'}
              </p>
            ) : (
              <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
                <table className="w-full text-left text-sm">
                  <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                    <tr>
                      <th scope="col" className="w-10 px-4 py-3">
                        <input
                          type="checkbox"
                          checked={
                            docs.items.length > 0 &&
                            docs.items.every((d) => selectedDocs.includes(d.id))
                          }
                          onChange={toggleAll}
                          aria-label="Select all documents on this page"
                          className="h-4 w-4"
                        />
                      </th>
                      <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">
                        Title
                      </th>
                      <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">
                        Accession
                      </th>
                      <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">
                        Date
                      </th>
                      <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">
                        Completeness
                      </th>
                      <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">
                        Status
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                    {docs.items.map((doc) => (
                      <tr
                        key={doc.id}
                        className="hover:bg-gray-50 dark:hover:bg-gray-700/50"
                      >
                        <td className="px-4 py-3">
                          <input
                            type="checkbox"
                            checked={selectedDocs.includes(doc.id)}
                            onChange={() => toggleDoc(doc.id)}
                            aria-label={`Select document: ${doc.title}`}
                            className="h-4 w-4"
                          />
                        </td>
                        <td className="px-4 py-3">
                          <Link
                            to={`/archive/documents/${doc.id}`}
                            className="text-blue-700 dark:text-blue-400 hover:underline font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded"
                          >
                            {doc.title}
                          </Link>
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                          {doc.accession_number ?? '\u2014'}
                        </td>
                        <td className="px-4 py-3 text-gray-600 dark:text-gray-400">
                          {doc.date_display ?? '\u2014'}
                        </td>
                        <td className="px-4 py-3">
                          <CompletenessBadge level={doc.description_completeness} />
                        </td>
                        <td className="px-4 py-3">
                          <span className="text-xs capitalize text-gray-500 dark:text-gray-400">
                            {doc.description_status}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Pagination */}
            {docs.pages > 1 && (
              <nav aria-label="Document pagination" className="mt-4 flex items-center justify-center gap-2">
                <button
                  type="button"
                  disabled={page <= 1}
                  onClick={() => setSearchParams((prev) => { prev.set('page', String(page - 1)); return prev; })}
                  className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
                  aria-label="Previous page"
                >
                  Previous
                </button>
                <span className="text-sm text-gray-600 dark:text-gray-400" aria-current="page">
                  Page {docs.page} of {docs.pages}
                </span>
                <button
                  type="button"
                  disabled={page >= docs.pages}
                  onClick={() => setSearchParams((prev) => { prev.set('page', String(page + 1)); return prev; })}
                  className="min-h-[44px] px-3 py-1 rounded border border-gray-300 dark:border-gray-600 text-sm disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)]"
                  aria-label="Next page"
                >
                  Next
                </button>
              </nav>
            )}
          </>
        )}
      </main>

      {/* Bulk Action Toolbar */}
      <BulkToolbar
        selectedIds={selectedDocs}
        onClear={() => setSelectedDocs([])}
        onAction={handleBulkAction}
      />
    </div>
  );
}
