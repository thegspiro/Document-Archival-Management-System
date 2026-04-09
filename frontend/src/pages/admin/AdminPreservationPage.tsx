export default function AdminPreservationPage() {
  return (
    <div className="max-w-7xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Preservation Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-sm font-medium text-gray-500">Total Files</h2>
          <p className="mt-2 text-3xl font-bold text-gray-900">--</p>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-sm font-medium text-gray-500">Last Fixity Check</h2>
          <p className="mt-2 text-3xl font-bold text-gray-900">--</p>
        </div>
        <div className="bg-white shadow rounded-lg p-6">
          <h2 className="text-sm font-medium text-gray-500">Integrity Failures</h2>
          <p className="mt-2 text-3xl font-bold text-red-600">--</p>
        </div>
      </div>

      <div className="space-y-6">
        <section className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Format Inventory</h2>
          </div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Format (PRONOM)</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">PUID</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File Count</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total Size</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td colSpan={4} className="px-6 py-8 text-center text-gray-500">
                  Loading format inventory...
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <section className="bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold">Fixity Check Report</h2>
            <button
              type="button"
              className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
            >
              Run Fixity Check Now
            </button>
          </div>
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">File</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Checked At</th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Outcome</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              <tr>
                <td colSpan={3} className="px-6 py-8 text-center text-gray-500">
                  No fixity checks recorded yet.
                </td>
              </tr>
            </tbody>
          </table>
        </section>

        <section className="bg-white shadow rounded-lg p-6">
          <h2 className="text-lg font-semibold mb-4">Description Completeness</h2>
          <div className="grid grid-cols-4 gap-4 text-center">
            <div>
              <div className="text-2xl font-bold text-gray-400">--</div>
              <div className="text-sm text-gray-500">None</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-amber-600">--</div>
              <div className="text-sm text-gray-500">Minimal</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-blue-600">--</div>
              <div className="text-sm text-gray-500">Standard</div>
            </div>
            <div>
              <div className="text-2xl font-bold text-green-600">--</div>
              <div className="text-sm text-gray-500">Full</div>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
