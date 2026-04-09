import { useParams, Link } from 'react-router-dom';

export default function PublicExhibitPage() {
  const { slug, pageSlug } = useParams<{ slug: string; pageSlug?: string }>();

  return (
    <div className="max-w-7xl mx-auto">
      <nav className="mb-4 text-sm text-gray-500" aria-label="Breadcrumb">
        <Link to="/public" className="hover:text-blue-600">Home</Link>
        <span className="mx-2">/</span>
        <Link to="/public/exhibits" className="hover:text-blue-600">Exhibitions</Link>
        <span className="mx-2">/</span>
        <span className="text-gray-900">{slug}</span>
        {pageSlug && (
          <>
            <span className="mx-2">/</span>
            <span className="text-gray-900">{pageSlug}</span>
          </>
        )}
      </nav>

      <article>
        <header className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Exhibition: {slug}</h1>
          <p className="text-lg text-gray-600">Loading exhibition details...</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          <nav className="lg:col-span-1" aria-label="Exhibition pages">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wider">Pages</h2>
            <div className="bg-white shadow rounded-lg p-4">
              <p className="text-sm text-gray-500">Loading pages...</p>
            </div>
          </nav>

          <div className="lg:col-span-3">
            <div className="bg-white shadow rounded-lg p-8">
              <p className="text-gray-500">Loading page content...</p>
            </div>
          </div>
        </div>
      </article>
    </div>
  );
}
