// Global state management using Zustand for authentication state

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { User, Organization } from '@/types/api';
import { authService } from '@/lib/auth';
import { APP_CONFIG } from '@/lib/constants';

interface AuthState {
  // State
  user: User | null;
  organization: Organization | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;

  // Actions
  login: (email: string, password: string) => Promise<void>;
  register: (userData: {
    email: string;
    password: string;
    full_name: string;
    organization_name: string;
  }) => Promise<void>;
  logout: () => Promise<void>;
  refreshToken: () => Promise<void>;
  updateUser: (userData: Partial<User>) => Promise<void>;
  setOrganization: (organization: Organization) => void;
  clearError: () => void;
  initialize: () => Promise<void>;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial state
      user: null,
      organization: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,

      // Login action
      login: async (email: string, password: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await authService.login({ email, password });
          
          set({
            user: response.user,
            organization: response.organization,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.detail || 'Ошибка входа в систему',
          });
          throw error;
        }
      },

      // Register action
      register: async (userData) => {
        set({ isLoading: true, error: null });
        
        try {
          await authService.register(userData);
          set({ isLoading: false, error: null });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.detail || 'Ошибка регистрации',
          });
          throw error;
        }
      },

      // Logout action
      logout: async () => {
        set({ isLoading: true });
        
        try {
          await authService.logout();
        } catch (error) {
          console.warn('Logout error:', error);
        } finally {
          set({
            user: null,
            organization: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },

      // Refresh token action
      refreshToken: async () => {
        try {
          await authService.refreshToken();
          // Token is automatically updated in localStorage
          // No need to update state as it's handled by the API interceptor
        } catch (error) {
          // If refresh fails, logout user
          get().logout();
          throw error;
        }
      },

      // Update user action
      updateUser: async (userData: Partial<User>) => {
        set({ isLoading: true, error: null });
        
        try {
          const updatedUser = await authService.updateProfile(userData);
          
          set({
            user: updatedUser,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.detail || 'Ошибка обновления профиля',
          });
          throw error;
        }
      },

      // Set organization action
      setOrganization: (organization: Organization) => {
        set({ organization });
        authService.setOrganizationData(organization);
      },

      // Clear error action
      clearError: () => {
        set({ error: null });
      },

      // Initialize action (check auth state on app start)
      initialize: async () => {
        set({ isLoading: true });
        
        try {
          // Check if user is authenticated
          if (authService.isAuthenticated() && !authService.isTokenExpired()) {
            // Try to get current user data
            const user = await authService.getCurrentUser();
            const organization = authService.getOrganizationData();
            
            set({
              user,
              organization,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } else {
            // Clear auth data if token is expired or invalid
            authService.clearAuthData();
            set({
              user: null,
              organization: null,
              isAuthenticated: false,
              isLoading: false,
              error: null,
            });
          }
        } catch (error) {
          // If initialization fails, clear auth data
          authService.clearAuthData();
          set({
            user: null,
            organization: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      },
    }),
    {
      name: 'auth-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        user: state.user,
        organization: state.organization,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);

// Selectors for common use cases
export const useAuth = () => {
  const store = useAuthStore();
  return {
    user: store.user,
    organization: store.organization,
    isAuthenticated: store.isAuthenticated,
    isLoading: store.isLoading,
    error: store.error,
    login: store.login,
    logout: store.logout,
    clearError: store.clearError,
  };
};

export const useUser = () => {
  const store = useAuthStore();
  return {
    user: store.user,
    updateUser: store.updateUser,
  };
};

export const useOrganization = () => {
  const store = useAuthStore();
  return {
    organization: store.organization,
    setOrganization: store.setOrganization,
  };
};
