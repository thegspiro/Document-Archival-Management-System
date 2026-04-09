/**
 * Edit form for document metadata. Loads the document, presents all
 * editable ISAD(G) fields, and submits updates via PATCH.
 * Uses react-hook-form with Zod validation for all fields.
 */
import { useEffect, useRef } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { z } from 'zod';
import { zodResolver } from '@hookform/resolvers/zod';
import { documentsApi } from '../../api/documents';
import Spinner from '../../components/ui/Spinner';
import type { Document, DocumentUpdate } from '../../types/api';

const LEVEL_OPTIONS = ['fonds', 'subfonds', 'series', 'subseries', 'file', 'item'] as const;
const COPYRIGHT_OPTIONS = ['copyrighted', 'public_domain', 'unknown', 'orphan_work', 'creative_commons'] as const;
const DESCRIPTION_STATUS_OPTIONS = ['draft', 'revised', 'final'] as const;

/**
 * ISO date string regex for YYYY-MM-DD format.
 * Used to validate normalized date fields.
 */
const ISO_DATE_REGEX = /^\d{4}-\d{2}-\d{2}$/;

/**
 * ISO 639 language code pattern. Accepts comma-separated 2 or 3 letter codes
 * (e.g., "eng", "eng,fra", "en+fr").
 */
const LANGUAGE_CODE_REGEX = /^[a-zA-Z]{2,3}([,+][a-zA-Z]{2,3})*$/;

const documentEditSchema = z.object({
  title: z.string().min(1, 'Title is required.'),
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
  access_conditions: z.string().optional().default(''),
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
  rights_holder: z.string().optional().default(''),
  rights_note: z.string().optional().default(''),
  description_status: z.enum(DESCRIPTION_STATUS_OPTIONS, {
    errorMap: () => ({ message: 'Invalid description status.' }),
  }),
  is_public: z.boolean(),
  has_content_advisory: z.boolean(),
  content_advisory_note: z.string().optional().default(''),
  geo_location_name: z.string().optional().default(''),
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

type DocumentEditFormData = z.infer<typeof documentEditSchema>;

export default function DocumentEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const documentId = Number(id);
  const errorSummaryRef = useRef<HTMLDivElement>(null);

  const { data: doc, isLoading, isError } = useQuery<Document>({
    queryKey: ['documents', documentId],
    queryFn: () => documentsApi.get(documentId),
    enabled: !Number.isNaN(documentId),
  });

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
    setError,
  } = useForm<DocumentEditFormData>({
    resolver: zodResolver(documentEditSchema),
    defaultValues: {
      title: '',
      date_display: '',
      date_start: '',
      date_end: '',
      level_of_description: 'item',
      extent: '',
      scope_and_content: '',
      access_conditions: '',
      language_of_material: '',
      copyright_status: 'unknown',
      rights_holder: '',
      rights_note: '',
      description_status: 'draft',
      is_public: false,
      has_content_advisory: false,
      content_advisory_note: '',
      geo_location_name: '',
    },
  });

  useEffect(() => {
    if (doc) {
      reset({
        title: doc.title ?? '',
        date_display: doc.date_display ?? '',
        date_start: doc.date_start ?? '',
        date_end: doc.date_end ?? '',
        level_of_description: (doc.level_of_description as typeof LEVEL_OPTIONS[number]) ?? 'item',
        extent: doc.extent ?? '',
        scope_and_content: doc.scope_and_content ?? '',
        access_conditions: doc.access_conditions ?? '',
        language_of_material: doc.language_of_material ?? '',
        copyright_status: (doc.copyright_status as typeof COPYRIGHT_OPTIONS[number]) ?? 'unknown',
        rights_holder: doc.rights_holder ?? '',
        rights_note: doc.rights_note ?? '',
        description_status: (doc.description_status as typeof DESCRIPTION_STATUS_OPTIONS[number]) ?? 'draft',
        is_public: doc.is_public,
        has_content_advisory: doc.has_content_advisory,
        content_advisory_note: doc.content_advisory_note ?? '',
        geo_location_name: doc.geo_location_name ?? '',
      });
    }
  }, [doc, reset]);

  const mutation = useMutation({
    mutationFn: (data: DocumentUpdate) => documentsApi.update(documentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', documentId] });
      navigate(`/archive/documents/${documentId}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError('root', { message: detail ?? 'Failed to save changes.' });
      errorSummaryRef.current?.focus();
    },
  });

  const onSubmit = (data: DocumentEditFormData) => {
    const payload: DocumentUpdate = {
      title: data.title.trim(),
      date_display: data.date_display || null,
      date_start: data.date_start || null,
      date_end: data.date_end || null,
      level_of_description: data.level_of_description,
      extent: data.extent || null,
      scope_and_content: data.scope_and_content || null,
      access_conditions: data.access_conditions || null,
      language_of_material: data.language_of_material || null,
      copyright_status: data.copyright_status,
      rights_holder: data.rights_holder || null,
      rights_note: data.rights_note || null,
      is_public: data.is_public,
      has_content_advisory: data.has_content_advisory,
      content_advisory_note: data.content_advisory_note || null,
      geo_location_name: data.geo_location_name || null,
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

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner label="Loading document" />
      </div>
    );
  }

  if (isError || !doc) {
    return (
      <div className="p-6 max-w-3xl mx-auto">
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
          Failed to load document.
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <nav aria-label="Breadcrumb" className="text-sm text-gray-500 dark:text-gray-400 mb-2">
        <Link to="/archive" className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
          Archive
        </Link>
        <span aria-hidden="true"> / </span>
        <Link to={`/archive/documents/${doc.id}`} className="hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
          {doc.accession_number ?? `Document #${doc.id}`}
        </Link>
        <span aria-hidden="true"> / </span>
        <span aria-current="page">Edit</span>
      </nav>

      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Edit Document</h1>

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
          <fieldset>
            <legend className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Identity Statement</legend>
            <div className="space-y-4">
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

              {/* Level of description */}
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

              {/* Extent */}
              <div>
                <label htmlFor="extent" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Extent</label>
                <input
                  id="extent"
                  type="text"
                  placeholder='"3 pages", "1 photograph"'
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                  {...register('extent')}
                />
              </div>
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Content and Structure</legend>
            <div className="space-y-4">
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
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Access and Rights</legend>
            <div className="space-y-4">
              {/* Access conditions */}
              <div>
                <label htmlFor="access_conditions" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Access conditions</label>
                <textarea
                  id="access_conditions"
                  rows={2}
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                  {...register('access_conditions')}
                />
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

              {/* Rights holder */}
              <div>
                <label htmlFor="rights_holder" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Rights holder</label>
                <input
                  id="rights_holder"
                  type="text"
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                  {...register('rights_holder')}
                />
              </div>

              {/* Rights note */}
              <div>
                <label htmlFor="rights_note" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Rights note</label>
                <textarea
                  id="rights_note"
                  rows={2}
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                  {...register('rights_note')}
                />
              </div>
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Description Control</legend>
            <div className="space-y-4">
              {/* Description status */}
              <div>
                <label htmlFor="description_status" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Description status</label>
                <select
                  id="description_status"
                  aria-invalid={errors.description_status ? 'true' : undefined}
                  aria-describedby={errors.description_status ? 'description_status-error' : undefined}
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                  {...register('description_status')}
                >
                  {DESCRIPTION_STATUS_OPTIONS.map((opt) => <option key={opt} value={opt}>{opt}</option>)}
                </select>
                {errors.description_status && <p id="description_status-error" className="mt-1 text-sm text-red-600 dark:text-red-400">{errors.description_status.message}</p>}
              </div>
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Publication and Advisory</legend>
            <div className="space-y-4">
              {/* Is public */}
              <div className="flex items-center gap-3">
                <input
                  id="is_public"
                  type="checkbox"
                  className="h-5 w-5 rounded border-gray-300 dark:border-gray-600 text-blue-700 focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                  {...register('is_public')}
                />
                <label htmlFor="is_public" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Publicly visible
                </label>
              </div>

              {/* Content advisory */}
              <div className="flex items-center gap-3">
                <input
                  id="has_content_advisory"
                  type="checkbox"
                  className="h-5 w-5 rounded border-gray-300 dark:border-gray-600 text-blue-700 focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                  {...register('has_content_advisory')}
                />
                <label htmlFor="has_content_advisory" className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Has content advisory
                </label>
              </div>

              {/* Content advisory note */}
              <div>
                <label htmlFor="content_advisory_note" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Content advisory note</label>
                <textarea
                  id="content_advisory_note"
                  rows={2}
                  aria-describedby="content_advisory_note-hint"
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                  {...register('content_advisory_note')}
                />
                <p id="content_advisory_note-hint" className="mt-1 text-xs text-gray-500 dark:text-gray-400">Institution-authored contextual note. Displayed when content advisory is enabled.</p>
              </div>

              {/* Geo location name */}
              <div>
                <label htmlFor="geo_location_name" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Location name</label>
                <input
                  id="geo_location_name"
                  type="text"
                  placeholder="e.g., Falls Church, VA"
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
                  {...register('geo_location_name')}
                />
              </div>
            </div>
          </fieldset>

          <div className="flex items-center gap-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <button type="submit" disabled={mutation.isPending}
              className="min-h-[44px] px-6 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
              {mutation.isPending ? 'Saving...' : 'Save Changes'}
            </button>
            <Link to={`/archive/documents/${doc.id}`}
              className="min-h-[44px] inline-flex items-center px-4 py-2 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
              Cancel
            </Link>
          </div>
        </div>
      </form>
    </div>
  );
}
