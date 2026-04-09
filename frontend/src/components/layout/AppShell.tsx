/** Authenticated layout: skip nav + navbar + sidebar + main content area. */
import { Outlet } from 'react-router-dom';
import SkipNav from '../ui/SkipNav';
import Navbar from './Navbar';
import Sidebar from './Sidebar';
import ToastContainer from '../ui/Toast';
import SessionTimeout from '../ui/SessionTimeout';
import { useUIStore } from '../../stores/ui';

export default function AppShell() {
  const { sidebarOpen } = useUIStore();

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      <SkipNav />
      {/* ARIA live region for dynamic announcements */}
      <div id="aria-live-region" aria-live="polite" aria-atomic="true" className="sr-only" />

      <Navbar />
      <div className="flex">
        <Sidebar />
        <main
          id="main-content"
          className={`flex-1 p-6 transition-all ${sidebarOpen ? 'ml-64' : 'ml-0'}`}
          role="main"
        >
          <Outlet />
        </main>
      </div>
      <ToastContainer />
      <SessionTimeout />
    </div>
  );
}
