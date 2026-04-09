import { Link } from 'react-router-dom';

export default function PublicCollectionsPage() {
  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">Collections</h1>
      <p className="text-gray-600 mb-8">
        Browse the archival collections available for public research.
      </p>

      <div className="space-y-4">
        <div className="bg-white shadow rounded-lg p-6 text-center text-gray-500">
          <p>No public collections available at this time.</p>
          <Link to="/public" className="mt-2 inline-block text-blue-600 hover:text-blue-800">
            Return to home
          </Link>
        </div>
      </div>
    </div>
  );
}
