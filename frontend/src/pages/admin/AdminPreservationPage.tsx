/**
 * Preservation dashboard. Shows format inventory, fixity check results,
 * and preservation event log.
 */
import { useQuery, useMutation } from '@tanstack/react-query';
import apiClient from '../../api/client';
import Spinner from '../../components/ui/Spinner';

interface FormatEntry { format_name: string; count: number; puid: string | null }
interface FixityReport { total_checked: number; matches: number; mismatches: number; missing: number; last_run: string | null }

export default function AdminPreservationPage() {
  const formatQuery = useQuery<FormatEntry[]>({
    queryKey: ['admin', 'format-inventory'],
    queryFn: () => apiClient.get('/admin/format-inventory').then((r) => r.data),
  });

  const fixityQuery = useQuery<FixityReport>({
    queryKey: ['admin', 'fixity-report'],
    queryFn: () => apiClient.get('/admin/fixity-report').then((r) => r.data),
  });

  const fixityRunMutation = useMutation({
    mutationFn: () => apiClient.post('/admin/fixity-run'),
  });

  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Preservation Dashboard</h1>

      {/* Fixity Report */}
      <section aria-labelledby="fixity-heading" className="mb-8">
        <div className="flex items-center justify-between mb-3">
          <h2 id="fixity-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100">Fixity Check Report</h2>
          <button type="button" onClick={() => fixityRunMutation.mutate()} disabled={fixityRunMutation.isPending}
            className="min-h-[44px] px-4 py-2 rounded bg-blue-700 hover:bg-blue-800 text-white text-sm font-medium disabled:opacity-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
            {fixityRunMutation.isPending ? 'Running...' : 'Run Fixity Check Now'}
          </button>
        </div>
        {fixityQuery.isLoading && <Spinner size="sm" label="Loading fixity report" />}
        {fixityQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load fixity report.</p>}
        {fixityQuery.data && (
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{fixityQuery.data.total_checked}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Total Checked</p>
            </div>
            <div className="bg-white dark:bg-gray-800 border border-green-200 dark:border-green-800 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-green-700 dark:text-green-400">{fixityQuery.data.matches}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Matches</p>
            </div>
            <div className="bg-white dark:bg-gray-800 border border-red-200 dark:border-red-800 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-red-700 dark:text-red-400">{fixityQuery.data.mismatches}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Mismatches</p>
            </div>
            <div className="bg-white dark:bg-gray-800 border border-amber-200 dark:border-amber-800 rounded-lg p-4 text-center">
              <p className="text-2xl font-bold text-amber-700 dark:text-amber-400">{fixityQuery.data.missing}</p>
              <p className="text-xs text-gray-500 dark:text-gray-400">Missing</p>
            </div>
          </div>
        )}
        {fixityQuery.data?.last_run && (
          <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
            Last run: <time dateTime={fixityQuery.data.last_run}>{new Date(fixityQuery.data.last_run).toLocaleString()}</time>
          </p>
        )}
      </section>

      {/* Format Inventory */}
      <section aria-labelledby="format-heading">
        <h2 id="format-heading" className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3">Format Inventory</h2>
        {formatQuery.isLoading && <Spinner size="sm" label="Loading format inventory" />}
        {formatQuery.isError && <p className="text-red-600 dark:text-red-400 text-sm">Failed to load format inventory.</p>}
        {formatQuery.data && formatQuery.data.length === 0 && <p className="text-gray-500 dark:text-gray-400 text-sm">No files in the repository yet.</p>}
        {formatQuery.data && formatQuery.data.length > 0 && (
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
            <table className="w-full text-left text-sm">
              <thead className="bg-gray-50 dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700">
                <tr>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">Format</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium">PUID</th>
                  <th scope="col" className="px-4 py-3 text-gray-500 dark:text-gray-400 font-medium text-right">Count</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100 dark:divide-gray-700">
                {formatQuery.data.map((entry, i) => (
                  <tr key={i} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <td className="px-4 py-3 text-gray-900 dark:text-gray-100">{entry.format_name}</td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400 font-mono text-xs">{entry.puid ?? '\u2014'}</td>
                    <td className="px-4 py-3 text-right text-gray-900 dark:text-gray-100 font-medium">{entry.count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
