import { useParams, Link } from 'react-router-dom';

export default function PublicDocumentPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="max-w-7xl mx-auto">
      <nav className="mb-4 text-sm text-gray-500" aria-label="Breadcrumb">
        <Link to="/public" className="hover:text-blue-600">Home</Link>
        <span className="mx-2">/</span>
        <Link to="/public/search" className="hover:text-blue-600">Documents</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">Document #{id}</span>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <div
            className="bg-gray-100 rounded-lg flex items-center justify-center"
            style={{ minHeight: '500px' }}
            role="region"
            aria-label="Document viewer"
          >
            <p className="text-gray-500">Loading document viewer...</p>
          </div>

          <nav className="flex justify-between mt-4" aria-label="Document pages">
            <button
              type="button"
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Previous page"
              disabled
            >
              Previous
            </button>
            <span className="text-sm text-gray-500 self-center" aria-current="page">Page 1 of 1</span>
            <button
              type="button"
              className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              aria-label="Next page"
              disabled
            >
              Next
            </button>
          </nav>
        </div>

        <aside className="lg:col-span-1 space-y-6">
          <section className="bg-white shadow rounded-lg p-6">
            <h1 className="text-xl font-bold text-gray-900 mb-4">Document Metadata</h1>
            <dl className="space-y-3">
              <div>
                <dt className="text-sm font-medium text-gray-500">Title</dt>
                <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Date</dt>
                <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Creator</dt>
                <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Accession Number</dt>
                <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Description</dt>
                <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
              </div>
            </dl>
          </section>

          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Citation</h2>
            <div className="space-y-2">
              <label htmlFor="cite-format" className="block text-sm font-medium text-gray-700">Format</label>
              <select id="cite-format" className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="chicago_note">Chicago (Note)</option>
                <option value="chicago_bib">Chicago (Bibliography)</option>
                <option value="turabian">Turabian</option>
                <option value="bibtex">BibTeX</option>
                <option value="ris">RIS</option>
              </select>
              <div className="mt-2 p-3 bg-gray-50 rounded text-sm text-gray-700 italic">
                Citation will appear here.
              </div>
            </div>
          </section>

          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Transcript</h2>
            <p className="text-sm text-gray-500">Loading transcript...</p>
          </section>
        </aside>
      </div>
    </div>
  );
}
