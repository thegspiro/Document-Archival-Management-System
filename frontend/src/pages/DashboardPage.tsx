/**
 * Dashboard page showing recent activity, review queue count, inbox count,
 * collection stats, and description completeness overview.
 */
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import apiClient from '../api/client';

interface DashboardStats {
  total_documents: number;
  inbox_count: number;
  review_queue_count: number;
  public_documents: number;
  total_collections: number;
  completeness: {
    none: number;
    minimal: number;
    standard: number;
    full: number;
  };
}

interface RecentActivity {
  id: number;
  action: string;
  resource_type: string | null;
  resource_id: number | null;
  detail: Record<string, unknown> | null;
  created_at: string;
}

function StatCard({
  label,
  value,
  href,
  color = 'blue',
}: {
  label: string;
  value: number;
  href?: string;
  color?: string;
}) {
  const colorMap: Record<string, string> = {
    blue: 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800',
    amber: 'bg-amber-50 dark:bg-amber-900/20 border-amber-200 dark:border-amber-800',
    green: 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800',
    purple: 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800',
  };

  const content = (
    <div className={`rounded-lg border p-4 ${colorMap[color] ?? colorMap.blue}`}>
      <p className="text-sm text-gray-600 dark:text-gray-400">{label}</p>
      <p className="text-3xl font-bold text-gray-900 dark:text-gray-100 mt-1">{value}</p>
    </div>
  );

  if (href) {
    return (
      <Link to={href} className="block focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2 rounded-lg">
        {content}
      </Link>
    );
  }
  return content;
}

function CompletenessBar({ completeness }: { completeness: DashboardStats['completeness'] }) {
  const total =
    completeness.none + completeness.minimal + completeness.standard + completeness.full;
  if (total === 0) return <p className="text-sm text-gray-500 dark:text-gray-400">No documents yet.</p>;

  const segments = [
    { key: 'full', label: 'Full', count: completeness.full, color: 'bg-green-600' },
    { key: 'standard', label: 'Standard', count: completeness.standard, color: 'bg-blue-600' },
    { key: 'minimal', label: 'Minimal', count: completeness.minimal, color: 'bg-amber-500' },
    { key: 'none', label: 'None', count: completeness.none, color: 'bg-gray-400' },
  ];

  return (
    <div>
      <div
        className="flex h-4 rounded-full overflow-hidden"
        role="img"
        aria-label={`Description completeness: ${segments.map((s) => `${s.label}: ${s.count}`).join(', ')}`}
      >
        {segments.map(
          (seg) =>
            seg.count > 0 && (
              <div
                key={seg.key}
                className={seg.color}
                style={{ width: `${(seg.count / total) * 100}%` }}
              />
            ),
        )}
      </div>
      <div className="flex gap-4 mt-2 text-xs text-gray-600 dark:text-gray-400">
        {segments.map((seg) => (
          <span key={seg.key} className="flex items-center gap-1">
            <span className={`inline-block w-3 h-3 rounded-sm ${seg.color}`} aria-hidden="true" />
            {seg.label}: {seg.count}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function DashboardPage() {
  const statsQuery = useQuery<DashboardStats>({
    queryKey: ['dashboard', 'stats'],
    queryFn: () => apiClient.get('/reports/collection').then((r) => r.data),
  });

  const activityQuery = useQuery<RecentActivity[]>({
    queryKey: ['dashboard', 'activity'],
    queryFn: () =>
      apiClient.get('/audit-log', { params: { per_page: 10 } }).then((r) => r.data.items ?? r.data),
  });

  const stats = statsQuery.data;

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Dashboard</h1>

      {statsQuery.isLoading && (
        <div role="status" aria-label="Loading dashboard" className="text-center py-12">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-r-transparent" aria-hidden="true" />
          <p className="mt-2 text-gray-500 dark:text-gray-400">Loading dashboard...</p>
        </div>
      )}

      {statsQuery.isError && (
        <div role="alert" className="p-4 rounded bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-800 text-red-800 dark:text-red-200">
          Failed to load dashboard data. Please try refreshing.
        </div>
      )}

      {stats && (
        <>
          {/* Stat Cards */}
          <section aria-labelledby="stats-heading" className="mb-8">
            <h2 id="stats-heading" className="sr-only">
              Collection statistics
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
              <StatCard label="Total Documents" value={stats.total_documents} color="blue" />
              <StatCard label="Inbox" value={stats.inbox_count} href="/archive/inbox" color="amber" />
              <StatCard
                label="Review Queue"
                value={stats.review_queue_count}
                href="/review"
                color="purple"
              />
              <StatCard label="Published" value={stats.public_documents} color="green" />
            </div>
          </section>

          {/* Completeness */}
          <section aria-labelledby="completeness-heading" className="mb-8">
            <h2
              id="completeness-heading"
              className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3"
            >
              Description Completeness
            </h2>
            <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
              <CompletenessBar completeness={stats.completeness} />
            </div>
          </section>
        </>
      )}

      {/* Recent Activity */}
      <section aria-labelledby="activity-heading">
        <h2
          id="activity-heading"
          className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-3"
        >
          Recent Activity
        </h2>
        <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
          {activityQuery.isLoading && (
            <p className="p-4 text-gray-500 dark:text-gray-400">Loading activity...</p>
          )}
          {activityQuery.isError && (
            <p className="p-4 text-red-600 dark:text-red-400">Failed to load activity.</p>
          )}
          {activityQuery.data && activityQuery.data.length === 0 && (
            <p className="p-4 text-gray-500 dark:text-gray-400">No recent activity.</p>
          )}
          {activityQuery.data && activityQuery.data.length > 0 && (
            <ul className="divide-y divide-gray-100 dark:divide-gray-700">
              {activityQuery.data.map((entry) => (
                <li key={entry.id} className="px-4 py-3 flex justify-between items-start">
                  <div>
                    <p className="text-sm text-gray-900 dark:text-gray-100">
                      <span className="font-medium">{entry.action}</span>
                      {entry.resource_type && (
                        <span className="text-gray-500 dark:text-gray-400">
                          {' '}
                          on {entry.resource_type} #{entry.resource_id}
                        </span>
                      )}
                    </p>
                  </div>
                  <time
                    className="text-xs text-gray-400 dark:text-gray-500 whitespace-nowrap ml-4"
                    dateTime={entry.created_at}
                  >
                    {new Date(entry.created_at).toLocaleString()}
                  </time>
                </li>
              ))}
            </ul>
          )}
        </div>
      </section>
    </div>
  );
}
