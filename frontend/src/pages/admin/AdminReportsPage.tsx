/**
 * Reports selection page. Links to all available report types.
 */
import { Link } from 'react-router-dom';

const REPORTS = [
  {
    title: 'Accession Report',
    description: 'New accessions by date range, collection, and user. Designed for annual reports and NHPRC grant reporting.',
    href: '/admin/reports/accessions',
    apiEndpoint: '/api/v1/reports/accessions',
  },
  {
    title: 'Processing Progress',
    description: 'Description completeness distribution per collection. Identifies backlogs and processing priorities.',
    href: '/admin/reports/processing',
    apiEndpoint: '/api/v1/reports/processing',
  },
  {
    title: 'User Activity',
    description: 'Per-user document creation, updates, and contributions over time.',
    href: '/admin/reports/users',
    apiEndpoint: '/api/v1/reports/users',
  },
  {
    title: 'Collection Summary',
    description: 'Total documents, files, storage, OCR coverage, and completeness distribution.',
    href: '/admin/reports/collection',
    apiEndpoint: '/api/v1/reports/collection',
  },
  {
    title: 'Public Access Summary',
    description: 'Published documents, exhibitions, and public engagement metrics.',
    href: '/admin/reports/public-access',
    apiEndpoint: '/api/v1/reports/public-access',
  },
];

export default function AdminReportsPage() {
  return (
    <div className="p-6 max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-6">Reports</h1>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {REPORTS.map((report) => (
          <Link key={report.href} to={report.href}
            className="block bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-5 hover:shadow-md transition-shadow focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--color-focus,#005fcc)] focus-visible:ring-offset-2">
            <h2 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">{report.title}</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400">{report.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
