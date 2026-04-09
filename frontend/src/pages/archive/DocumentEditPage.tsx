/**
 * Edit form for document metadata. Loads the document, presents all
 * editable ISAD(G) fields, and submits updates via PATCH.
 */
import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { documentsApi } from '../../api/documents';
import Spinner from '../../components/ui/Spinner';
import type { Document, DocumentUpdate } from '../../types/api';

interface FormState {
  title: string;
  date_display: string;
  date_start: string;
  date_end: string;
  level_of_description: string;
  extent: string;
  scope_and_content: string;
  access_conditions: string;
  language_of_material: string;
  copyright_status: string;
  rights_holder: string;
  rights_note: string;
  is_public: boolean;
  has_content_advisory: boolean;
  content_advisory_note: string;
  geo_location_name: string;
}

const LEVEL_OPTIONS = ['fonds', 'subfonds', 'series', 'subseries', 'file', 'item'];
const COPYRIGHT_OPTIONS = ['copyrighted', 'public_domain', 'unknown', 'orphan_work', 'creative_commons'];

export default function DocumentEditPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const documentId = Number(id);

  const { data: doc, isLoading, isError } = useQuery<Document>({
    queryKey: ['documents', documentId],
    queryFn: () => documentsApi.get(documentId),
    enabled: !Number.isNaN(documentId),
  });

  const [form, setForm] = useState<FormState>({
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
    is_public: false,
    has_content_advisory: false,
    content_advisory_note: '',
    geo_location_name: '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (doc) {
      setForm({
        title: doc.title ?? '',
        date_display: doc.date_display ?? '',
        date_start: doc.date_start ?? '',
        date_end: doc.date_end ?? '',
        level_of_description: doc.level_of_description ?? 'item',
        extent: doc.extent ?? '',
        scope_and_content: doc.scope_and_content ?? '',
        access_conditions: doc.access_conditions ?? '',
        language_of_material: doc.language_of_material ?? '',
        copyright_status: doc.copyright_status ?? 'unknown',
        rights_holder: doc.rights_holder ?? '',
        rights_note: doc.rights_note ?? '',
        is_public: doc.is_public,
        has_content_advisory: doc.has_content_advisory,
        content_advisory_note: doc.content_advisory_note ?? '',
        geo_location_name: doc.geo_location_name ?? '',
      });
    }
  }, [doc]);

  const mutation = useMutation({
    mutationFn: (data: DocumentUpdate) => documentsApi.update(documentId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents', documentId] });
      navigate(`/archive/documents/${documentId}`);
    },
    onError: (err: unknown) => {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setErrors({ _form: detail ?? 'Failed to save changes.' });
    },
  });

  const handleChange = (field: keyof FormState, value: string | boolean) => {
    setForm((prev) => ({ ...prev, [field]: value }));
    setErrors((prev) => {
      const next = { ...prev };
      delete next[field];
      delete next._form;
      return next;
    });
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: Record<string, string> = {};
    if (!form.title.trim()) {
      newErrors.title = 'Title is required.';
    }
    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }
    const payload: DocumentUpdate = {
      title: form.title.trim(),
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

      {errors._form && (
        <div role="alert" className="mb-4 p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
          {errors._form}
        </div>
      )}

      <form onSubmit={handleSubmit} noValidate>
        <div className="space-y-6">
          <fieldset>
            <legend className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Identity Statement</legend>
            <div className="space-y-4">
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
                  placeholder='"3 pages", "1 photograph"'
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
              </div>
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Content and Structure</legend>
            <div className="space-y-4">
              <div>
                <label htmlFor="scope_and_content" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Scope and content</label>
                <textarea id="scope_and_content" value={form.scope_and_content} onChange={(e) => handleChange('scope_and_content', e.target.value)}
                  rows={4}
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
              </div>
              <div>
                <label htmlFor="language_of_material" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Language of material</label>
                <input id="language_of_material" type="text" value={form.language_of_material} onChange={(e) => handleChange('language_of_material', e.target.value)}
                  placeholder="e.g., eng, eng+fra"
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
              </div>
            </div>
          </fieldset>

          <fieldset>
            <legend className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">Access and Rights</legend>
            <div className="space-y-4">
              <div>
                <label htmlFor="access_conditions" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Access conditions</label>
                <textarea id="access_conditions" value={form.access_conditions} onChange={(e) => handleChange('access_conditions', e.target.value)}
                  rows={2}
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]" />
              </div>
              <div>
                <label htmlFor="copyright_status" className="block text-sm font-medium text-gray-700 dark:text-gray-300">Copyright status</label>
                <select id="copyright_status" value={form.copyright_status} onChange={(e) => handleChange('copyright_status', e.target.value)}
                  className="mt-1 block w-full rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]">
                  {COPYRIGHT_OPTIONS.map((opt) => <option key={opt} value={opt}>{opt.replace(/_/g, ' ')}</option>)}
                </select>
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
