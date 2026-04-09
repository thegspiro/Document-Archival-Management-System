/** Public site layout: header + footer + content. No auth required. */
import { Outlet, Link } from 'react-router-dom';
import SkipNav from '../ui/SkipNav';

export default function PublicShell() {
  return (
    <div className="min-h-screen flex flex-col bg-white dark:bg-gray-900">
      <SkipNav />
      <div id="aria-live-region" aria-live="polite" aria-atomic="true" className="sr-only" />

      <header role="banner" className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm">
        <nav aria-label="Public navigation" className="max-w-7xl mx-auto px-4 flex items-center justify-between h-16">
          <Link to="/public" className="text-xl font-bold text-primary-700 dark:text-primary-400">
            ADMS Archive
          </Link>
          <div className="flex items-center gap-6">
            <Link to="/public/exhibits" className="text-sm text-gray-700 hover:text-primary-600 dark:text-gray-300 min-h-touch flex items-center">
              Exhibitions
            </Link>
            <Link to="/public/collections" className="text-sm text-gray-700 hover:text-primary-600 dark:text-gray-300 min-h-touch flex items-center">
              Collections
            </Link>
            <Link to="/public/search" className="text-sm text-gray-700 hover:text-primary-600 dark:text-gray-300 min-h-touch flex items-center">
              Search
            </Link>
          </div>
        </nav>
      </header>

      <main id="main-content" className="flex-1" role="main">
        <Outlet />
      </main>

      <footer role="contentinfo" className="bg-gray-50 dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700 py-8">
        <div className="max-w-7xl mx-auto px-4 text-center text-sm text-gray-500 dark:text-gray-400">
          <p>Powered by ADMS — Archival Document Management System</p>
        </div>
      </footer>
    </div>
  );
}
