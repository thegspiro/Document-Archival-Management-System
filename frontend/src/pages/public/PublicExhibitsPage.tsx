import { useState } from 'react';
import { Link } from 'react-router-dom';

export default function PublicExhibitsPage() {
  const [search, setSearch] = useState('');

  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Exhibitions</h1>
      <p className="text-gray-600 mb-8">Browse our curated exhibitions of historical documents and primary sources.</p>

      <div className="mb-6">
        <label htmlFor="exhibit-search" className="sr-only">Search exhibitions</label>
        <input
          id="exhibit-search"
          type="search"
          placeholder="Search exhibitions..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full max-w-md rounded-md border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        <div className="bg-white shadow rounded-lg overflow-hidden text-center p-8">
          <p className="text-gray-500">No published exhibitions available at this time.</p>
          <Link to="/public" className="mt-2 inline-block text-blue-600 hover:text-blue-800">
            Return to home
          </Link>
        </div>
      </div>
    </div>
  );
}
