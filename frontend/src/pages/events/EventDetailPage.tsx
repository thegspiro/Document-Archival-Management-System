import { useParams, Link } from 'react-router-dom';

export default function EventDetailPage() {
  const { id } = useParams<{ id: string }>();

  return (
    <div className="max-w-7xl mx-auto">
      <nav className="mb-4 text-sm text-gray-500" aria-label="Breadcrumb">
        <Link to="/events" className="hover:text-blue-600">Events</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">Event #{id}</span>
      </nav>

      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold">Event Detail</h1>
        <Link
          to={`/events/${id}/edit`}
          className="inline-flex items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
        >
          Edit Event
        </Link>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Event Information</h2>
            <dl className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <dt className="text-sm font-medium text-gray-500">Title</dt>
                <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Type</dt>
                <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Date</dt>
                <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
              </div>
              <div>
                <dt className="text-sm font-medium text-gray-500">Location</dt>
                <dd className="mt-1 text-sm text-gray-900">Loading...</dd>
              </div>
            </dl>
          </section>

          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Linked Documents</h2>
            <p className="text-sm text-gray-500">No documents linked to this event yet.</p>
          </section>
        </div>

        <div className="space-y-6">
          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">People</h2>
            <p className="text-sm text-gray-500">No people linked to this event yet.</p>
          </section>

          <section className="bg-white shadow rounded-lg p-6">
            <h2 className="text-lg font-semibold mb-4">Locations</h2>
            <p className="text-sm text-gray-500">No locations linked to this event yet.</p>
          </section>
        </div>
      </div>
    </div>
  );
}
