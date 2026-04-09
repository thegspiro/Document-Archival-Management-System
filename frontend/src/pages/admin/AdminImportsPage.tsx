/**
 * CSV import management page. Lists import jobs and shows status.
 * Integrates the ColumnMapper component for mapped-mode imports.
 */
import { useState, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';
import ColumnMapper from '../../components/ui/ColumnMapper';

interface CsvImport {
  id: number;
  filename: string;
  import_mode: string;
  status: string;
  total_rows: number;
  valid_rows: number;
  error_rows: number;
  imported_rows: number;
  column_mapping: Record<string, string> | null;
  created_at: string;
}

interface UploadedImportResponse {
  id: number;
  filename: string;
  import_mode: string;
  status: string;
  csv_headers: string[];
  sample_rows: Record<string, string>[];
}

/** Inline upload and mapping workflow for mapped-mode imports. */
function MappedImportWorkflow({ onComplete }: { onComplete: () => void }) {
  const [step, setStep] = useState<'upload' | 'mapping' | 'submitting'>('upload');
  const [uploadResult, setUploadResult] = useState<UploadedImportResponse | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const queryClient = useQueryClient();

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('import_mode', 'mapped');
      const res = await apiClient.post('/admin/imports', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      return res.data as UploadedImportResponse;
    },
    onSuccess: (data) => {
      setUploadResult(data);
      setStep('mapping');
      setUploadError(null);
    },
    onError: () => {
      setUploadError('Failed to upload CSV file. Please check the file format and try again.');
    },
  });

  const mappingMutation = useMutation({
    mutationFn: async (mapping: Record<string, string>) => {
      if (!uploadResult) return;
      await apiClient.patch(`/admin/imports/${uploadResult.id}`, { column_mapping: mapping });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['admin', 'imports'] });
      onComplete();
    },
  });

  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) {
        uploadMutation.mutate(file);
      }
    },
    [uploadMutation],
  );

  const handleMappingComplete = useCallback(
    (mapping: Record<string, string>) => {
      setStep('submitting');
      mappingMutation.mutate(mapping);
    },
    [mappingMutation],
  );

  if (step === 'upload') {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
          Upload CSV for Mapped Import
        </h2>
        <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
          Upload your CSV file. You will then map each column to an ADMS field.
        </p>
        <div className="flex items-center gap-4">
          <label
            htmlFor="csv-upload-mapped"
            className="min-h-[44px] inline-flex items-center px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm cursor-pointer focus-within:ring-2 focus-within:ring-[var(--color-focus,#005fcc)] focus-within:ring-offset-2"
          >
            Choose CSV File
            <input
              id="csv-upload-mapped"
              type="file"
              accept=".csv,.tsv,.txt"
              className="sr-only"
              onChange={handleFileChange}
              disabled={uploadMutation.isPending}
            />
          </label>
          {uploadMutation.isPending && <Spinner label="Uploading file" />}
        </div>
        {uploadError && (
          <div role="alert" className="mt-4 p-3 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 text-sm">
            {uploadError}
          </div>
        )}
        <button
          type="button"
          onClick={onComplete}
          className="mt-4 text-sm text-gray-500 dark:text-gray-400 hover:underline focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)] rounded"
        >
          Cancel
        </button>
      </div>
    );
  }

  if (step === 'mapping' && uploadResult) {
    return (
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
            Map Columns: {uploadResult.filename}
          </h2>
          <button
            type="button"
            onClick={onComplete}
            className="min-h-[44px] px-3 py-2 text-sm text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-700 rounded focus:outline-none focus:ring-2 focus:ring-[var(--color-focus,#005fcc)]"
          >
            Cancel
          </button>
        </div>
        <ColumnMapper
          csvHeaders={uploadResult.csv_headers}
          sampleRows={uploadResult.sample_rows}
          onMappingComplete={handleMappingComplete}
        />
        {mappingMutation.isError && (
          <div role="alert" className="mt-4 p-3 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200 text-sm">
            Failed to save column mapping. Please try again.
          </div>
        )}
      </div>
    );
  }

  if (step === 'submitting') {
    return (
      <div className="flex items-center justify-center py-16">
        <Spinner label="Saving column mapping" />
      </div>
    );
  }

  return null;
}

function StatusBadge({ status }: { status: string }) {
  const styles: Record<string, string> = {
    uploaded: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-400',
    validating: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
    validation_failed: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300',
    ready: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
    importing: 'bg-blue-100 dark:bg-blue-900/40 text-blue-700 dark:text-blue-300',
    complete: 'bg-green-100 dark:bg-green-900/40 text-green-700 dark:text-green-300',
    failed: 'bg-red-100 dark:bg-red-900/40 text-red-700 dark:text-red-300',
  };
  return (
    <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${styles[status] ?? styles.uploaded}`}>
      {status.replace(/_/g, ' ')}
    </span>
  );
}

export default function AdminImportsPage() {
  const [showMappedImport, setShowMappedImport] = useState(false);
  const queryClient = useQueryClient();

  const { data, isLoading, isError } = useQuery<{ items: CsvImport[] }>({
    queryKey: ['admin', 'imports'],
    queryFn: () => apiClient.get('/admin/imports').then((r) => r.data),
  });

  const handleMappedImportComplete = useCallback(() => {
    setShowMappedImport(false);
    queryClient.invalidateQueries({ queryKey: ['admin', 'imports'] });
  }, [queryClient]);

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">CSV Imports</h1>
        <div className="flex gap-2">
          <a href="/api/v1/admin/imports/template" download
            className="min-h-[44px] inline-flex items-center px-4 py-2 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
            Download Template
          </a>
          <button
            type="button"
            onClick={() => setShowMappedImport(true)}
            className="min-h-[44px] inline-flex items-center px-4 py-2 rounded border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 text-sm hover:bg-gray-50 dark:hover:bg-gray-700 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
            Mapped Import
          </button>
          <Link to="/admin/imports/new"
            className="min-h-[44px] inline-flex items-center px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white font-medium text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
            Upload CSV
          </Link>
        </div>
      </div>

      {showMappedImport && (
        <div className="mb-6">
          <MappedImportWorkflow onComplete={handleMappedImportComplete} />
        </div>
      )}

      {isLoading && <div className="flex items-center justify-center py-16"><Spinner label="Loading imports" /></div>}
      {isError && <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">Failed to load imports.</div>}

      {data && (!data.items || data.items.length === 0) && (
        <div className="text-center py-16">
          <p className="text-gray-500 dark:text-gray-400 text-lg">No import jobs yet.</p>
          <p className="text-gray-400 dark:text-gray-500 text-sm mt-2">Upload a CSV file to begin importing documents.</p>
        </div>
      )}

      {data && data.items && data.items.length > 0 && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <table className="w-full text-left text-sm">
            <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Filename</th>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Mode</th>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Status</th>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Rows</th>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Date</th>
                <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium"><span className="sr-only">Actions</span></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
              {data.items.map((job) => (
                <tr key={job.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                  <td className="px-4 py-3 font-medium text-gray-900 dark:text-gray-100">{job.filename}</td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400 capitalize text-xs">{job.import_mode}</td>
                  <td className="px-4 py-3"><StatusBadge status={job.status} /></td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400 text-xs">
                    {job.imported_rows}/{job.total_rows}
                    {job.error_rows > 0 && <span className="text-red-600 dark:text-red-400"> ({job.error_rows} errors)</span>}
                  </td>
                  <td className="px-4 py-3 text-gray-600 dark:text-gray-400 text-xs">
                    <time dateTime={job.created_at}>{new Date(job.created_at).toLocaleDateString()}</time>
                  </td>
                  <td className="px-4 py-3">
                    <Link to={`/admin/imports/${job.id}`}
                      className="text-blue-700 dark:text-blue-400 hover:underline text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] rounded">
                      View
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
