import { useState } from 'react';
import { Link } from 'react-router-dom';

export default function ReviewListPage() {
  const [search, setSearch] = useState('');

  return (
    <div className="max-w-7xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">Review Queue</h1>
        <span className="text-sm text-gray-500 dark:text-gray-400">Documents awaiting review</span>
      </div>

      <div className="mb-4 flex gap-4">
        <div className="flex-1 max-w-md">
          <label htmlFor="review-search" className="sr-only">Search review queue</label>
          <input
            id="review-search"
            type="search"
            placeholder="Search by title or accession number..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            aria-label="Search review queue"
          />
        </div>
        <select
          aria-label="Filter by reason"
          className="rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm"
        >
          <option value="">All reasons</option>
          <option value="llm_suggestions">LLM Suggestions</option>
          <option value="manual_flag">Manual Flag</option>
          <option value="import">Import</option>
          <option value="initial_review">Initial Review</option>
          <option value="integrity_failure">Integrity Failure</option>
        </select>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200 dark:border-gray-700">
        <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
          <thead className="bg-gray-50 dark:bg-gray-800">
            <tr>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Document</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reason</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Priority</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Assigned To</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date Added</th>
              <th scope="col" className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900">
            <tr>
              <td colSpan={6} className="px-4 py-8 text-center text-sm text-gray-500 dark:text-gray-400">
                No documents pending review.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}
