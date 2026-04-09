import { Link } from 'react-router-dom';

export default function AdminReportsPage() {
  const reports = [
    {
      title: 'Accession Report',
      description: 'New accessions by date range. Designed for annual reports, NHPRC grant reporting, and board presentations.',
      href: '/admin/reports/accessions',
    },
    {
      title: 'Processing Progress',
      description: 'Per-collection breakdown of documents at each completeness level, identifying processing backlogs.',
      href: '/admin/reports/processing',
    },
    {
      title: 'User Activity',
      description: 'Per-user counts of documents created, updated, and other actions. For recognizing contributions and demonstrating activity.',
      href: '/admin/reports/users',
    },
    {
      title: 'Collection Summary',
      description: 'Total documents, files, storage usage, OCR completion rates, and description completeness distribution.',
      href: '/admin/reports/collection',
    },
    {
      title: 'Public Access Summary',
      description: 'Documents published, exhibitions published, and download counts. For demonstrating public value.',
      href: '/admin/reports/public-access',
    },
  ];

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Reports</h1>
      <p className="text-gray-600 mb-8">
        Generate reports for grant reporting, board presentations, and collection assessments.
        All reports can be exported as CSV and PDF.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {reports.map((report) => (
          <Link
            key={report.href}
            to={report.href}
            className="block bg-white shadow rounded-lg p-6 hover:shadow-md transition-shadow focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            <h2 className="text-lg font-semibold text-gray-900 mb-2">{report.title}</h2>
            <p className="text-sm text-gray-600">{report.description}</p>
          </Link>
        ))}
      </div>
    </div>
  );
}
