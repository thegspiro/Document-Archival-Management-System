/**
 * Create new document form. Collects minimal required fields and
 * submits via POST to create a new document record.
 */
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../../api/documents';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import type { DocumentCreate, ArrangementNode } from '../../types/api';

const LEVEL_OPTIONS = ['fonds', 'subfonds', 'series', 'subseries', 'file', 'item'];

export default function DocumentNewPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const nodesQuery = useQuery<ArrangementNode[]>({
    queryKey: ['nodes', 'flat'],
    queryFn: () => apiClient.get('/nodes').then((r) => r.data),
  });

  const [form, setForm] = useState({
    title: '',
    arrangement_node_id: '',
    date_display: '',
    date_start: '',
    date_end: '',
    level_of_description: 'item',
    extent: '',
    scope_and_content: '',
    language_of_material: '',
    copyright_status: 'unknown',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const mutation = useMutation({
    mutationFn: (data: DocumentCreate) => documentsApi.create(data),
    onSuccess: (doc) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      navigate(`/archive/documents/${doc.id}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrors({ _form: detail ?? 'Failed to create document.' });
    },
  });

  const handleChange = (field: string, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => { const next = { ...prev }; delete next[field]; delete next._form; return next; });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    if (!form.title.trim()) newErrors.title = 'Title is required.';
    if (Object.keys(newErrors).length > 0) { setErrors(newErrors); return; }
    const payload: DocumentCreate = {
      title: form.title.trim(),
      arrangement_node_id: form.arrangement_node_id ? Number(form.arrangement_node_id) : null,
      date_display: form.date_display || null,
      date_start: form.date_start || null,
      date_end: form.date_end || null,
      level_of_description: form.level_of_description,
      extent: form.extent || null,
      scope_and_content: form.scope_and_content || null,
      language_of_material: form.language_of_material || null,
      copyright_status: form.copyright_status,
    };
    mutation.mutate(payload);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <nav aria-label="Breadcrumb" className="text-sm text-gray-500 dark:text-gray-400 mb-2">
        <Link to="/archive" className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">Archive</Link>
        <span aria-hidden="true"> / </span>
        <span aria-current="page">New Document</span>
      </nav>

      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Create New Document</h1>

      {errors._form && (
        <div role="alert" className="mb-4 p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">{errors._form}</div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="space-y-6">
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Title <span className="text-red-600" aria-hidden="true">*</span><span className="sr-only">(required)</span>
            </label>
            <input id="title" type="text" value={form.title} onChange={(e) => handleChange('title', e.target.value)}
              aria-required="true" aria-invalid={!!errors.title} aria-describedby={errors.title ? 'title-error' : undefined}
              className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
            {errors.title && <p id="title-error" className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.title}</p>}
          </div>

          <div>
            <label htmlFor="arrangement_node_id" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Collection</label>
            {nodesQuery.isLoading && <Spinner size="sm" label="Loading collections" />}
            <select id="arrangement_node_id" value={form.arrangement_node_id} onChange={(e) => handleChange('arrangement_node_id', e.target.value)}
              className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]">
              <option value="">No collection</option>
              {nodesQuery.data && Array.isArray(nodesQuery.data) && nodesQuery.data.map((node) => (
                <option key={node.id} value={node.id}>{node.title} ({node.level_type})</option>
              ))}
            </select>
          </div>

          <div>
            <label htmlFor="date_display" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Date (display)</label>
            <input id="date_display" type="text" value={form.date_display} onChange={(e) => handleChange('date_display', e.target.value)}
              placeholder="e.g., circa 1920, January 5, 1887"
              className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="date_start" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Date start</label>
              <input id="date_start" type="date" value={form.date_start} onChange={(e) => handleChange('date_start', e.target.value)}
                className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
            </div>
            <div>
              <label htmlFor="date_end" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Date end</label>
              <input id="date_end" type="date" value={form.date_end} onChange={(e) => handleChange('date_end', e.target.value)}
                className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="level_of_description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Level of description</label>
              <select id="level_of_description" value={form.level_of_description} onChange={(e) => handleChange('level_of_description', e.target.value)}
                className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]">
                {LEVEL_OPTIONS.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
              </select>
            </div>
            <div>
              <label htmlFor="extent" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Extent</label>
              <input id="extent" type="text" value={form.extent} onChange={(e) => handleChange('extent', e.target.value)}
                placeholder='"3 pages"'
                className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
            </div>
          </div>

          <div>
            <label htmlFor="scope_and_content" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Scope and content</label>
            <textarea id="scope_and_content" value={form.scope_and_content} onChange={(e) => handleChange('scope_and_content', e.target.value)}
              rows={4}
              className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
          </div>

          <div className="flex items-center gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button type="submit" disabled={mutation.isPending}
              className="min-h-[44px] px-6 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
              {mutation.isPending ? 'Creating...' : 'Create Document'}
            </button>
            <Link to="/archive"
              className="min-h-[44px] inline-flex items-center px-4 py-2 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
              Cancel
            </Link>
          </div>
        </div>
      </form>
    </div>
  );
}
