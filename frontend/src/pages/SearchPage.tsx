import { useState } from 'react';

export default function SearchPage() {
  const [query, setQuery] = useState('');

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Search Archive</h1>

      <form className="mb-6" onSubmit={(e) => e.preventDefault()}>
        <div className="flex gap-2">
          <label htmlFor="search-query" className="sr-only">Search documents</label>
          <input
            id="search-query"
            type="search"
            placeholder="Search by title, content, accession number..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="rounded-md bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Search
          </button>
        </div>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <aside className="md:col-span-1">
          <h2 className="text-sm font-semibold text-gray-700 mb-3">Filters</h2>
          <div className="space-y-4 bg-white shadow rounded-lg p-4">
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Document Type</label>
              <select className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm" aria-label="Filter by document type">
                <option value="">All types</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Date From</label>
              <input type="date" className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm" aria-label="Date from" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Date To</label>
              <input type="date" className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm" aria-label="Date to" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Review Status</label>
              <select className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm" aria-label="Filter by review status">
                <option value="">Any</option>
                <option value="pending">Pending</option>
                <option value="approved">Approved</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>
        </aside>

        <div className="md:col-span-3">
          <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
            Enter a search query to find documents.
          </div>
        </div>
      </div>
    </div>
  );
}
