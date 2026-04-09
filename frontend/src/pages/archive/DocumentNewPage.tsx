/**
 * Create new document form. Collects required and optional fields and
 * submits via POST to create a new document record.
 * Uses react-hook-form with Zod validation for all fields.
 */
import { useRef } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { documentsApi } from '../../api/documents';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import type { DocumentCreate, ArrangementNode } from '../../types/api';

const LEVEL_OPTIONS = ['fonds', 'subfonds', 'series', 'subseries', 'file', 'item'] as const;
const COPYRIGHT_OPTIONS = ['copyrighted', 'public_domain', 'unknown', 'orphan_work', 'creative_commons'] as const;

/**
 * ISO date string regex for YYYY-MM-DD format.
 */
const ISO_DATE_REGEX = /^\d{4}-\d{2}-\d{2}$/;

/**
 * ISO 639 language code pattern. Accepts comma-separated 2 or 3 letter codes.
 */
const LANGUAGE_CODE_REGEX = /^[a-zA-Z]{2,3}([,+][a-zA-Z]{2,3})*$/;

const documentNewSchema = z.object({
  title: z.string().min(1, 'Title is required.'),
  arrangement_node_id: z.string().optional().default(''),
  date_display: z.string().optional().default(''),
  date_start: z
    .string()
    .optional()
    .default('')
    .refine((val) => !val || ISO_DATE_REGEX.test(val), {
      message: 'Date start must be a valid date (YYYY-MM-DD).',
    }),
  date_end: z
    .string()
    .optional()
    .default('')
    .refine((val) => !val || ISO_DATE_REGEX.test(val), {
      message: 'Date end must be a valid date (YYYY-MM-DD).',
    }),
  level_of_description: z.enum(LEVEL_OPTIONS, {
    errorMap: () => ({ message: 'Invalid level of description.' }),
  }),
  extent: z.string().optional().default(''),
  scope_and_content: z.string().optional().default(''),
  language_of_material: z
    .string()
    .optional()
    .default('')
    .refine((val) => !val || LANGUAGE_CODE_REGEX.test(val), {
      message: 'Language codes must be valid ISO 639 codes (e.g., "eng" or "eng,fra").',
    }),
  copyright_status: z.enum(COPYRIGHT_OPTIONS, {
    errorMap: () => ({ message: 'Invalid copyright status.' }),
  }),
}).refine(
  (data) => {
    if (data.date_start && data.date_end) {
      return data.date_end >= data.date_start;
    }
    return true;
  },
  {
    message: 'Date end must be on or after date start.',
    path: ['date_end'],
  }
);

type DocumentNewFormData = z.infer<typeof documentNewSchema>;

export default function DocumentNewPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const errorSummaryRef = useRef<HTMLDivElement>(null);

  const nodesQuery = useQuery<ArrangementNode[]>({
    queryKey: ['nodes', 'flat'],
    queryFn: () => apiClient.get('/nodes').then((r) => r.data),
  });

  const {
    register,
    handleSubmit,
    formState: { errors },
    setError,
  } = useForm<DocumentNewFormData>({
    resolver: zodResolver(documentNewSchema),
    defaultValues: {
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
    },
  });

  const mutation = useMutation({
    mutationFn: (data: DocumentCreate) => documentsApi.create(data),
    onSuccess: (doc) => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
      navigate(`/archive/documents/${doc.id}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError('root', { message: detail ?? 'Failed to create document.' });
      errorSummaryRef.current?.focus();
    },
  });

  const onSubmit = (data: DocumentNewFormData) => {
    const payload: DocumentCreate = {
      title: data.title.trim(),
      arrangement_node_id: data.arrangement_node_id ? Number(data.arrangement_node_id) : null,
      date_display: data.date_display || null,
      date_start: data.date_start || null,
      date_end: data.date_end || null,
      level_of_description: data.level_of_description,
      extent: data.extent || null,
      scope_and_content: data.scope_and_content || null,
      language_of_material: data.language_of_material || null,
      copyright_status: data.copyright_status,
    };
    mutation.mutate(payload);
  };

  const onInvalid = () => {
    errorSummaryRef.current?.focus();
  };

  /** Collect all field-level errors for the error summary. */
  const fieldErrors = Object.entries(errors)
    .filter(([key]) => key !== 'root')
    .map(([key, err]) => ({ field: key, message: err?.message ?? 'Invalid value.' }));

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <nav aria-label="Breadcrumb" className="text-sm text-gray-500 dark:text-gray-400 mb-2">
        <Link to="/archive" className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">Archive</Link>
        <span aria-hidden="true"> / </span>
        <span aria-current="page">New Document</span>
      </nav>

      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Create New Document</h1>

      {/* Error summary — focused on validation failure */}
      {(errors.root || fieldErrors.length > 0) && (
        <div
          ref={errorSummaryRef}
          role="alert"
          tabIndex={-1}
          className="mb-6 p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
        >
          {errors.root && <p className="font-medium mb-2">{errors.root.message}</p>}
          {fieldErrors.length > 0 && (
            <>
              <p className="font-medium mb-1">Please correct the following errors:</p>
              <ul className="list-disc pl-5 space-y-1 text-sm">
                {fieldErrors.map(({ field, message }) => (
                  <li key={field}>
                    <a href={`#${field}`} className="underline hover:no-underline">
                      {message}
                    </a>
                  </li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}

      <form onSubmit={handleSubmit(onSubmit, onInvalid)} noValidate>
        <div className="space-y-6">
          {/* Title */}
          <div>
            <label htmlFor="title" className="block text-sm font-medium text-gray-700 dark:text-gray-300">
              Title <span className="text-red-600" aria-hidden="true">*</span><span className="sr-only">(required)</span>
            </label>
            <input
              id="title"
              type="text"
              aria-required="true"
              aria-invalid={errors.title ? 'true' : undefined}
              aria-describedby={errors.title ? 'title-error' : undefined}
              className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
              {...register('title')}
            />
            {errors.title && <p id="title-error" className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.title.message}</p>}
          </div>

          {/* Collection */}
          <div>
            <label htmlFor="arrangement_node_id" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Collection</label>
            {nodesQuery.isLoading && <Spinner size="sm" label="Loading collections" />}
            <select
              id="arrangement_node_id"
              className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
              {...register('arrangement_node_id')}
            >
              <option value="">No collection</option>
              {nodesQuery.data && Array.isArray(nodesQuery.data) && nodesQuery.data.map((node) => (
                <option key={node.id} value={node.id}>{node.title} ({node.level_type})</option>
              ))}
            </select>
          </div>

          {/* Date display */}
          <div>
            <label htmlFor="date_display" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Date (display)</label>
            <input
              id="date_display"
              type="text"
              placeholder="e.g., circa 1920, January 5, 1887"
              aria-describedby="date_display-hint"
              className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
              {...register('date_display')}
            />
            <p id="date_display-hint" className="mt-1 text-xs text-gray-500 dark:text-gray-400">Free-text date as written on the document.</p>
          </div>

          {/* Date start / Date end */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="date_start" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Date start</label>
              <input
                id="date_start"
                type="date"
                aria-invalid={errors.date_start ? 'true' : undefined}
                aria-describedby={errors.date_start ? 'date_start-error' : undefined}
                className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                {...register('date_start')}
              />
              {errors.date_start && <p id="date_start-error" className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.date_start.message}</p>}
            </div>
            <div>
              <label htmlFor="date_end" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Date end</label>
              <input
                id="date_end"
                type="date"
                aria-invalid={errors.date_end ? 'true' : undefined}
                aria-describedby={errors.date_end ? 'date_end-error' : undefined}
                className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                {...register('date_end')}
              />
              {errors.date_end && <p id="date_end-error" className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.date_end.message}</p>}
            </div>
          </div>

          {/* Level of description + Extent */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label htmlFor="level_of_description" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Level of description</label>
              <select
                id="level_of_description"
                aria-invalid={errors.level_of_description ? 'true' : undefined}
                aria-describedby={errors.level_of_description ? 'level_of_description-error' : undefined}
                className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                {...register('level_of_description')}
              >
                {LEVEL_OPTIONS.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
              </select>
              {errors.level_of_description && <p id="level_of_description-error" className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.level_of_description.message}</p>}
            </div>
            <div>
              <label htmlFor="extent" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Extent</label>
              <input
                id="extent"
                type="text"
                placeholder='"3 pages"'
                className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                {...register('extent')}
              />
            </div>
          </div>

          {/* Scope and content */}
          <div>
            <label htmlFor="scope_and_content" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Scope and content</label>
            <textarea
              id="scope_and_content"
              rows={4}
              className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
              {...register('scope_and_content')}
            />
          </div>

          {/* Language of material */}
          <div>
            <label htmlFor="language_of_material" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Language of material</label>
            <input
              id="language_of_material"
              type="text"
              placeholder="e.g., eng, eng+fra"
              aria-invalid={errors.language_of_material ? 'true' : undefined}
              aria-describedby={errors.language_of_material ? 'language_of_material-error' : 'language_of_material-hint'}
              className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
              {...register('language_of_material')}
            />
            <p id="language_of_material-hint" className="mt-1 text-xs text-gray-500 dark:text-gray-400">ISO 639 codes, comma or plus separated.</p>
            {errors.language_of_material && <p id="language_of_material-error" className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.language_of_material.message}</p>}
          </div>

          {/* Copyright status */}
          <div>
            <label htmlFor="copyright_status" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Copyright status</label>
            <select
              id="copyright_status"
              aria-invalid={errors.copyright_status ? 'true' : undefined}
              aria-describedby={errors.copyright_status ? 'copyright_status-error' : undefined}
              className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
              {...register('copyright_status')}
            >
              {COPYRIGHT_OPTIONS.map((opt) => <option key={opt} value={opt}>{opt.replace(/_/g, ' ')}</option>)}
            </select>
            {errors.copyright_status && <p id="copyright_status-error" className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.copyright_status.message}</p>}
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
