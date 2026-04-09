import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from './context/ThemeContext';
import { useAuth } from './hooks/useAuth';

// Layouts
import AppShell from './components/layout/AppShell';
import PublicShell from './components/layout/PublicShell';

// Auth pages
import LoginPage from './pages/LoginPage';
import SetupPage from './pages/SetupPage';

// Authenticated pages
import DashboardPage from './pages/DashboardPage';
import ArchivePage from './pages/archive/ArchivePage';
import DocumentDetailPage from './pages/archive/DocumentDetailPage';
import DocumentEditPage from './pages/archive/DocumentEditPage';
import DocumentNewPage from './pages/archive/DocumentNewPage';
import InboxPage from './pages/inbox/InboxPage';
import ReviewListPage from './pages/review/ReviewListPage';
import ReviewDetailPage from './pages/review/ReviewDetailPage';
import PeoplePage from './pages/PeoplePage';
import PersonDetailPage from './pages/PersonDetailPage';
import LocationsPage from './pages/locations/LocationsPage';
import LocationDetailPage from './pages/locations/LocationDetailPage';
import EventsPage from './pages/events/EventsPage';
import EventDetailPage from './pages/events/EventDetailPage';
import VocabularyPage from './pages/VocabularyPage';
import ExhibitionsPage from './pages/ExhibitionsPage';
import SearchPage from './pages/SearchPage';

// Admin pages
import AdminUsersPage from './pages/admin/AdminUsersPage';
import AdminSettingsPage from './pages/admin/AdminSettingsPage';
import AdminPreservationPage from './pages/admin/AdminPreservationPage';
import AdminImportsPage from './pages/admin/AdminImportsPage';
import AdminReportsPage from './pages/admin/AdminReportsPage';

// Public pages
import PublicHomePage from './pages/public/PublicHomePage';
import PublicExhibitsPage from './pages/public/PublicExhibitsPage';
import PublicExhibitPage from './pages/public/PublicExhibitPage';
import PublicDocumentPage from './pages/public/PublicDocumentPage';
import PublicSearchPage from './pages/public/PublicSearchPage';
import PublicCollectionsPage from './pages/public/PublicCollectionsPage';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { user, isLoading } = useAuth();
  if (isLoading) return <div className="flex items-center justify-center h-screen">Loading...</div>;
  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <Routes>
          {/* Auth */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/setup/*" element={<SetupPage />} />

          {/* Authenticated app */}
          <Route path="/" element={<ProtectedRoute><AppShell /></ProtectedRoute>}>
            <Route index element={<Navigate to="/dashboard" replace />} />
            <Route path="dashboard" element={<DashboardPage />} />
            <Route path="archive" element={<ArchivePage />} />
            <Route path="archive/documents/new" element={<DocumentNewPage />} />
            <Route path="archive/documents/:id" element={<DocumentDetailPage />} />
            <Route path="archive/documents/:id/edit" element={<DocumentEditPage />} />
            <Route path="archive/inbox" element={<InboxPage />} />
            <Route path="review" element={<ReviewListPage />} />
            <Route path="review/:documentId" element={<ReviewDetailPage />} />
            <Route path="people" element={<PeoplePage />} />
            <Route path="people/:id" element={<PersonDetailPage />} />
            <Route path="locations" element={<LocationsPage />} />
            <Route path="locations/:id" element={<LocationDetailPage />} />
            <Route path="events" element={<EventsPage />} />
            <Route path="events/:id" element={<EventDetailPage />} />
            <Route path="vocabulary" element={<VocabularyPage />} />
            <Route path="exhibitions" element={<ExhibitionsPage />} />
            <Route path="search" element={<SearchPage />} />
            <Route path="admin/users" element={<AdminUsersPage />} />
            <Route path="admin/settings" element={<AdminSettingsPage />} />
            <Route path="admin/preservation" element={<AdminPreservationPage />} />
            <Route path="admin/imports" element={<AdminImportsPage />} />
            <Route path="admin/reports" element={<AdminReportsPage />} />
          </Route>

          {/* Public site */}
          <Route path="/public" element={<PublicShell />}>
            <Route index element={<PublicHomePage />} />
            <Route path="exhibits" element={<PublicExhibitsPage />} />
            <Route path="exhibits/:slug" element={<PublicExhibitPage />} />
            <Route path="exhibits/:slug/:pageSlug" element={<PublicExhibitPage />} />
            <Route path="documents/:id" element={<PublicDocumentPage />} />
            <Route path="search" element={<PublicSearchPage />} />
            <Route path="collections" element={<PublicCollectionsPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
