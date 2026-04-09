/** Auth store — current user, role, token refresh logic. */
import { create } from 'zustand';
import apiClient from '../api/client';
import type { User } from '../types/api';

interface AuthState {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  fetchUser: () => Promise<void>;
  hasRole: (...roles: string[]) => boolean;
}

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (email: string, password: string) => {
    const response = await apiClient.post('/auth/login', { email, password });
    set({ user: response.data.user, isAuthenticated: true, isLoading: false });
  },

  logout: async () => {
    try {
      await apiClient.post('/auth/logout');
    } finally {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  fetchUser: async () => {
    try {
      const response = await apiClient.get('/users/me');
      set({ user: response.data, isAuthenticated: true, isLoading: false });
    } catch {
      set({ user: null, isAuthenticated: false, isLoading: false });
    }
  },

  hasRole: (...roles: string[]) => {
    const { user } = get();
    if (!user) return false;
    if (user.is_superadmin) return true;
    return user.roles.some((r) => roles.includes(r.name));
  },
}));
