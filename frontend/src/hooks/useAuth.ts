/** Hook to access auth state. Reads from Zustand auth store. */
import { useEffect } from 'react';
import { useAuthStore } from '../stores/auth';

export function useAuth() {
  const { user, isLoading, isAuthenticated, fetchUser, login, logout, hasRole } = useAuthStore();

  useEffect(() => {
    if (!user && isLoading) {
      fetchUser();
    }
  }, [user, isLoading, fetchUser]);

  return { user, isLoading, isAuthenticated, login, logout, hasRole };
}
