import { useState } from 'react';
import { Link } from 'react-router-dom';

export default function PublicSearchPage() {
  const [query, setQuery] = useState('');

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Search the Archive</h1>

      <form className="mb-8" onSubmit={(e) => e.preventDefault()}>
        <div className="flex gap-2">
          <label htmlFor="public-search" className="sr-only">Search documents</label>
          <input
            id="public-search"
            type="search"
            placeholder="Search by title, content, creator, accession number..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="flex-1 rounded-md border border-gray-300 px-4 py-3 text-base focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="rounded-md bg-blue-600 px-8 py-3 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Search
          </button>
        </div>
      </form>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
        <aside className="md:col-span-1" role="group" aria-labelledby="filter-heading">
          <h2 id="filter-heading" className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">Filters</h2>
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
              <label className="block text-sm font-medium text-gray-600 mb-1">Creator</label>
              <input type="text" placeholder="Search creators..." className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm" aria-label="Filter by creator" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-600 mb-1">Language</label>
              <select className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm" aria-label="Filter by language">
                <option value="">All languages</option>
              </select>
            </div>
          </div>
        </aside>

        <div className="md:col-span-3">
          <div className="bg-white shadow rounded-lg p-8 text-center text-gray-500">
            <p>Enter a search query to find documents in the archive.</p>
            <p className="mt-2">
              Or <Link to="/public/collections" className="text-blue-600 hover:text-blue-800">browse collections</Link> to explore.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
