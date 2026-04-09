import { Link } from 'react-router-dom';

export default function PublicHomePage() {
  return (
    <div className="max-w-7xl mx-auto">
      <section className="text-center py-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Welcome to the Archive</h1>
        <p className="text-lg text-gray-600 max-w-2xl mx-auto mb-8">
          Explore our collection of historical documents, photographs, and primary sources.
        </p>
        <div className="flex justify-center gap-4">
          <Link
            to="/public/exhibits"
            className="inline-flex items-center rounded-md bg-blue-600 px-6 py-3 text-base font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Browse Exhibitions
          </Link>
          <Link
            to="/public/search"
            className="inline-flex items-center rounded-md border border-gray-300 bg-white px-6 py-3 text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          >
            Search Documents
          </Link>
        </div>
      </section>

      <section className="py-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Featured Exhibitions</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <div className="bg-white shadow rounded-lg overflow-hidden">
            <div className="h-48 bg-gray-200 flex items-center justify-center">
              <span className="text-gray-400">No exhibitions published yet</span>
            </div>
          </div>
        </div>
      </section>

      <section className="py-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Browse Collections</h2>
        <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
          <p>Public collections will appear here once they are published.</p>
          <Link to="/public/collections" className="mt-2 inline-block text-blue-600 hover:text-blue-800">
            View all collections
          </Link>
        </div>
      </section>
    </div>
  );
}
