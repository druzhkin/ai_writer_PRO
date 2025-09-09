// Organization state management for current organization context and member management

import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import { Organization, OrganizationMember, UsageStats } from '@/types/api';
import { api } from '@/lib/api';
import { API_ENDPOINTS, APP_CONFIG } from '@/lib/constants';

interface OrganizationState {
  // State
  currentOrganization: Organization | null;
  organizations: Organization[];
  members: OrganizationMember[];
  usageStats: UsageStats | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setCurrentOrganization: (organization: Organization) => void;
  loadOrganizations: () => Promise<void>;
  loadMembers: (organizationId: string) => Promise<void>;
  loadUsageStats: (organizationId: string) => Promise<void>;
  addMember: (organizationId: string, email: string, role: 'admin' | 'member') => Promise<void>;
  updateMemberRole: (organizationId: string, userId: string, role: 'admin' | 'member') => Promise<void>;
  removeMember: (organizationId: string, userId: string) => Promise<void>;
  updateOrganization: (organizationId: string, data: Partial<Organization>) => Promise<void>;
  clearError: () => void;
  clearData: () => void;
}

export const useOrganizationStore = create<OrganizationState>()(
  persist(
    (set, get) => ({
      // Initial state
      currentOrganization: null,
      organizations: [],
      members: [],
      usageStats: null,
      isLoading: false,
      error: null,

      // Set current organization
      setCurrentOrganization: (organization: Organization) => {
        set({ currentOrganization: organization });
        // Update localStorage
        localStorage.setItem(APP_CONFIG.STORAGE_KEYS.ORGANIZATION_DATA, JSON.stringify(organization));
      },

      // Load user's organizations
      loadOrganizations: async () => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get<Organization[]>(API_ENDPOINTS.ORGANIZATIONS.LIST);
          
          set({
            organizations: response.data,
            isLoading: false,
            error: null,
          });

          // Set current organization if not set
          const { currentOrganization } = get();
          if (!currentOrganization && response.data.length > 0) {
            get().setCurrentOrganization(response.data[0]);
          }
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.detail || 'Ошибка загрузки организаций',
          });
          throw error;
        }
      },

      // Load organization members
      loadMembers: async (organizationId: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get<OrganizationMember[]>(
            API_ENDPOINTS.ORGANIZATIONS.MEMBERS(organizationId)
          );
          
          set({
            members: response.data,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.detail || 'Ошибка загрузки участников',
          });
          throw error;
        }
      },

      // Load organization usage stats
      loadUsageStats: async (organizationId: string) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.get<UsageStats>(
            API_ENDPOINTS.ORGANIZATIONS.USAGE(organizationId)
          );
          
          set({
            usageStats: response.data,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.detail || 'Ошибка загрузки статистики',
          });
          throw error;
        }
      },

      // Add member to organization
      addMember: async (organizationId: string, email: string, role: 'admin' | 'member') => {
        set({ isLoading: true, error: null });
        
        try {
          await api.post(API_ENDPOINTS.ORGANIZATIONS.MEMBERS(organizationId), {
            email,
            role,
          });
          
          // Reload members list
          await get().loadMembers(organizationId);
          
          set({ isLoading: false, error: null });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.detail || 'Ошибка добавления участника',
          });
          throw error;
        }
      },

      // Update member role
      updateMemberRole: async (organizationId: string, userId: string, role: 'admin' | 'member') => {
        set({ isLoading: true, error: null });
        
        try {
          await api.put(API_ENDPOINTS.ORGANIZATIONS.MEMBER(organizationId, userId), {
            role,
          });
          
          // Update member in local state
          const { members } = get();
          const updatedMembers = members.map(member =>
            member.user_id === userId ? { ...member, role } : member
          );
          
          set({
            members: updatedMembers,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.detail || 'Ошибка обновления роли участника',
          });
          throw error;
        }
      },

      // Remove member from organization
      removeMember: async (organizationId: string, userId: string) => {
        set({ isLoading: true, error: null });
        
        try {
          await api.delete(API_ENDPOINTS.ORGANIZATIONS.MEMBER(organizationId, userId));
          
          // Remove member from local state
          const { members } = get();
          const updatedMembers = members.filter(member => member.user_id !== userId);
          
          set({
            members: updatedMembers,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.detail || 'Ошибка удаления участника',
          });
          throw error;
        }
      },

      // Update organization
      updateOrganization: async (organizationId: string, data: Partial<Organization>) => {
        set({ isLoading: true, error: null });
        
        try {
          const response = await api.put<Organization>(
            API_ENDPOINTS.ORGANIZATIONS.UPDATE(organizationId),
            data
          );
          
          // Update current organization if it's the one being updated
          const { currentOrganization } = get();
          if (currentOrganization?.id === organizationId) {
            get().setCurrentOrganization(response.data);
          }
          
          // Update in organizations list
          const { organizations } = get();
          const updatedOrganizations = organizations.map(org =>
            org.id === organizationId ? response.data : org
          );
          
          set({
            organizations: updatedOrganizations,
            isLoading: false,
            error: null,
          });
        } catch (error: any) {
          set({
            isLoading: false,
            error: error.detail || 'Ошибка обновления организации',
          });
          throw error;
        }
      },

      // Clear error
      clearError: () => {
        set({ error: null });
      },

      // Clear all data
      clearData: () => {
        set({
          currentOrganization: null,
          organizations: [],
          members: [],
          usageStats: null,
          isLoading: false,
          error: null,
        });
      },
    }),
    {
      name: 'organization-store',
      storage: createJSONStorage(() => localStorage),
      partialize: (state) => ({
        currentOrganization: state.currentOrganization,
        organizations: state.organizations,
      }),
    }
  )
);

// Selectors for common use cases
export const useCurrentOrganization = () => {
  const store = useOrganizationStore();
  return {
    organization: store.currentOrganization,
    setCurrentOrganization: store.setCurrentOrganization,
    updateOrganization: store.updateOrganization,
  };
};

export const useOrganizations = () => {
  const store = useOrganizationStore();
  return {
    organizations: store.organizations,
    loadOrganizations: store.loadOrganizations,
    isLoading: store.isLoading,
    error: store.error,
  };
};

export const useOrganizationMembers = () => {
  const store = useOrganizationStore();
  return {
    members: store.members,
    loadMembers: store.loadMembers,
    addMember: store.addMember,
    updateMemberRole: store.updateMemberRole,
    removeMember: store.removeMember,
    isLoading: store.isLoading,
    error: store.error,
  };
};

export const useOrganizationUsage = () => {
  const store = useOrganizationStore();
  return {
    usageStats: store.usageStats,
    loadUsageStats: store.loadUsageStats,
    isLoading: store.isLoading,
    error: store.error,
  };
};
