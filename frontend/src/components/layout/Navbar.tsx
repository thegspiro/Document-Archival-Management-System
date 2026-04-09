/** Top navigation with inbox badge, review count, user menu, and theme toggle. */
import { Link } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { useInbox } from '../../hooks/useInbox';
import { useTheme } from '../../context/ThemeContext';
import { useUIStore } from '../../stores/ui';

export default function Navbar() {
  const { user, logout } = useAuth();
  const inboxCount = useInbox();
  const { theme, setTheme } = useTheme();
  const { toggleSidebar } = useUIStore();

  return (
    <header
      role="banner"
      className="sticky top-0 z-40 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 shadow-sm"
    >
      <nav aria-label="Primary navigation" className="flex items-center justify-between px-4 h-14">
        <div className="flex items-center gap-4">
          <button
            onClick={toggleSidebar}
            aria-label="Toggle sidebar navigation"
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 min-h-touch min-w-touch flex items-center justify-center"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
          <Link to="/dashboard" className="text-lg font-bold text-primary-700 dark:text-primary-400">
            ADMS
          </Link>
        </div>

        <div className="flex items-center gap-3">
          <Link
            to="/search"
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 min-h-touch min-w-touch flex items-center justify-center"
            aria-label="Search"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </Link>

          <Link
            to="/archive/inbox"
            className="relative p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 min-h-touch min-w-touch flex items-center justify-center"
            aria-label={`Inbox${inboxCount > 0 ? `, ${inboxCount} unprocessed` : ''}`}
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
            </svg>
            {inboxCount > 0 && (
              <span className="absolute -top-1 -right-1 bg-red-500 text-white text-xs rounded-full px-1.5 py-0.5 min-w-[20px] text-center">
                {inboxCount}
              </span>
            )}
          </Link>

          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
            className="p-2 rounded-md hover:bg-gray-100 dark:hover:bg-gray-700 min-h-touch min-w-touch flex items-center justify-center"
          >
            {theme === 'dark' ? (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" />
              </svg>
            ) : (
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" />
              </svg>
            )}
          </button>

          {user && (
            <div className="flex items-center gap-2 pl-2 border-l border-gray-200 dark:border-gray-700">
              <span className="text-sm text-gray-700 dark:text-gray-300">{user.display_name}</span>
              <button
                onClick={() => logout()}
                className="text-sm text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200 p-1"
              >
                Log out
              </button>
            </div>
          )}
        </div>
      </nav>
    </header>
  );
}
