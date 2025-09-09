// React Query configuration and custom hooks for API data fetching

import { useQuery, useMutation, useQueryClient, UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { api } from '@/lib/api';
import { API_ENDPOINTS } from '@/lib/constants';
import {
  User,
  Organization,
  StyleProfile,
  GeneratedContent,
  UsageStats,
  ContentGenerationRequest,
  ContentGenerationResponse,
  ContentEditRequest,
  ContentEditResponse,
  StyleCreationRequest,
  StyleUpdateRequest,
  StyleAnalysisResponse,
  FileUploadResponse,
  PaginatedResponse,
  ContentSearchParams,
  StyleSearchParams,
} from '@/types/api';

// Query keys factory
export const queryKeys = {
  // User queries
  user: {
    profile: ['user', 'profile'] as const,
  },
  
  // Organization queries
  organization: {
    list: ['organizations'] as const,
    detail: (id: string) => ['organizations', id] as const,
    members: (id: string) => ['organizations', id, 'members'] as const,
    usage: (id: string) => ['organizations', id, 'usage'] as const,
  },
  
  // Style queries
  style: {
    list: (orgId: string) => ['organizations', orgId, 'styles'] as const,
    detail: (orgId: string, id: string) => ['organizations', orgId, 'styles', id] as const,
    analysis: (orgId: string, id: string) => ['organizations', orgId, 'styles', id, 'analysis'] as const,
  },
  
  // Content queries
  content: {
    list: (orgId: string) => ['organizations', orgId, 'content'] as const,
    detail: (orgId: string, id: string) => ['organizations', orgId, 'content', id] as const,
    iterations: (orgId: string, id: string) => ['organizations', orgId, 'content', id, 'iterations'] as const,
  },
} as const;

// User hooks
export const useUserProfile = (options?: UseQueryOptions<User>) => {
  return useQuery({
    queryKey: queryKeys.user.profile,
    queryFn: () => api.get<User>(API_ENDPOINTS.USERS.PROFILE).then(res => res.data),
    ...options,
  });
};

// Organization hooks
export const useOrganizations = (options?: UseQueryOptions<Organization[]>) => {
  return useQuery({
    queryKey: queryKeys.organization.list,
    queryFn: () => api.get<Organization[]>(API_ENDPOINTS.ORGANIZATIONS.LIST).then(res => res.data),
    ...options,
  });
};

export const useOrganization = (id: string, options?: UseQueryOptions<Organization>) => {
  return useQuery({
    queryKey: queryKeys.organization.detail(id),
    queryFn: () => api.get<Organization>(API_ENDPOINTS.ORGANIZATIONS.DETAIL(id)).then(res => res.data),
    enabled: !!id,
    ...options,
  });
};

export const useOrganizationMembers = (organizationId: string, options?: UseQueryOptions<any[]>) => {
  return useQuery({
    queryKey: queryKeys.organization.members(organizationId),
    queryFn: () => api.get<any[]>(API_ENDPOINTS.ORGANIZATIONS.MEMBERS(organizationId)).then(res => res.data),
    enabled: !!organizationId,
    ...options,
  });
};

export const useOrganizationUsage = (organizationId: string, options?: UseQueryOptions<UsageStats>) => {
  return useQuery({
    queryKey: queryKeys.organization.usage(organizationId),
    queryFn: () => api.get<UsageStats>(API_ENDPOINTS.ORGANIZATIONS.USAGE(organizationId)).then(res => res.data),
    enabled: !!organizationId,
    ...options,
  });
};

// Style hooks
export const useStyles = (organizationId: string, searchParams?: StyleSearchParams, options?: UseQueryOptions<StyleProfile[]>) => {
  return useQuery({
    queryKey: [...queryKeys.style.list(organizationId), searchParams],
    queryFn: () => {
      const params = new URLSearchParams();
      if (searchParams) {
        Object.entries(searchParams).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params.append(key, String(value));
          }
        });
      }
      const url = `${API_ENDPOINTS.STYLES.LIST(organizationId)}${params.toString() ? `?${params.toString()}` : ''}`;
      return api.get<StyleProfile[]>(url).then(res => res.data);
    },
    enabled: !!organizationId,
    ...options,
  });
};

export const useStyle = (organizationId: string, styleId: string, options?: UseQueryOptions<StyleProfile>) => {
  return useQuery({
    queryKey: queryKeys.style.detail(organizationId, styleId),
    queryFn: () => api.get<StyleProfile>(API_ENDPOINTS.STYLES.DETAIL(organizationId, styleId)).then(res => res.data),
    enabled: !!organizationId && !!styleId,
    ...options,
  });
};

export const useStyleAnalysis = (organizationId: string, styleId: string, options?: UseQueryOptions<StyleAnalysisResponse>) => {
  return useQuery({
    queryKey: queryKeys.style.analysis(organizationId, styleId),
    queryFn: () => api.get<StyleAnalysisResponse>(API_ENDPOINTS.STYLES.ANALYZE(organizationId, styleId)).then(res => res.data),
    enabled: !!organizationId && !!styleId,
    ...options,
  });
};

// Content hooks
export const useContent = (organizationId: string, searchParams?: ContentSearchParams, options?: UseQueryOptions<GeneratedContent[]>) => {
  return useQuery({
    queryKey: [...queryKeys.content.list(organizationId), searchParams],
    queryFn: () => {
      const params = new URLSearchParams();
      if (searchParams) {
        Object.entries(searchParams).forEach(([key, value]) => {
          if (value !== undefined && value !== null && value !== '') {
            params.append(key, String(value));
          }
        });
      }
      const url = `${API_ENDPOINTS.CONTENT.LIST(organizationId)}${params.toString() ? `?${params.toString()}` : ''}`;
      return api.get<GeneratedContent[]>(url).then(res => res.data);
    },
    enabled: !!organizationId,
    ...options,
  });
};

export const useContentDetail = (organizationId: string, contentId: string, options?: UseQueryOptions<GeneratedContent>) => {
  return useQuery({
    queryKey: queryKeys.content.detail(organizationId, contentId),
    queryFn: () => api.get<GeneratedContent>(API_ENDPOINTS.CONTENT.DETAIL(organizationId, contentId)).then(res => res.data),
    enabled: !!organizationId && !!contentId,
    ...options,
  });
};

export const useContentIterations = (organizationId: string, contentId: string, options?: UseQueryOptions<any[]>) => {
  return useQuery({
    queryKey: queryKeys.content.iterations(organizationId, contentId),
    queryFn: () => api.get<any[]>(API_ENDPOINTS.CONTENT.ITERATIONS(organizationId, contentId)).then(res => res.data),
    enabled: !!organizationId && !!contentId,
    ...options,
  });
};

// Mutation hooks
export const useCreateStyle = (organizationId: string, options?: UseMutationOptions<StyleProfile, Error, StyleCreationRequest>) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: StyleCreationRequest) => 
      api.post<StyleProfile>(API_ENDPOINTS.STYLES.CREATE(organizationId), data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.style.list(organizationId) });
    },
    ...options,
  });
};

export const useUpdateStyle = (organizationId: string, styleId: string, options?: UseMutationOptions<StyleProfile, Error, StyleUpdateRequest>) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: StyleUpdateRequest) => 
      api.put<StyleProfile>(API_ENDPOINTS.STYLES.UPDATE(organizationId, styleId), data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.style.list(organizationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.style.detail(organizationId, styleId) });
    },
    ...options,
  });
};

export const useDeleteStyle = (organizationId: string, styleId: string, options?: UseMutationOptions<void, Error, void>) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => api.delete(API_ENDPOINTS.STYLES.DELETE(organizationId, styleId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.style.list(organizationId) });
      queryClient.removeQueries({ queryKey: queryKeys.style.detail(organizationId, styleId) });
    },
    ...options,
  });
};

export const useGenerateContent = (organizationId: string, options?: UseMutationOptions<ContentGenerationResponse, Error, ContentGenerationRequest>) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: ContentGenerationRequest) => 
      api.post<ContentGenerationResponse>(API_ENDPOINTS.CONTENT.GENERATE(organizationId), data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.content.list(organizationId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.organization.usage(organizationId) });
    },
    ...options,
  });
};

export const useEditContent = (organizationId: string, contentId: string, options?: UseMutationOptions<ContentEditResponse, Error, ContentEditRequest>) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: ContentEditRequest) => 
      api.post<ContentEditResponse>(API_ENDPOINTS.CONTENT.EDIT(organizationId, contentId), data).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.content.detail(organizationId, contentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.content.iterations(organizationId, contentId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.organization.usage(organizationId) });
    },
    ...options,
  });
};

export const useDeleteContent = (organizationId: string, contentId: string, options?: UseMutationOptions<void, Error, void>) => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: () => api.delete(API_ENDPOINTS.CONTENT.DELETE(organizationId, contentId)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.content.list(organizationId) });
      queryClient.removeQueries({ queryKey: queryKeys.content.detail(organizationId, contentId) });
    },
    ...options,
  });
};

export const useUploadFile = (organizationId: string, options?: UseMutationOptions<FileUploadResponse, Error, File>) => {
  return useMutation({
    mutationFn: (file: File) => {
      const formData = new FormData();
      formData.append('file', file);
      return api.post<FileUploadResponse>(API_ENDPOINTS.FILES.UPLOAD(organizationId), formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }).then(res => res.data);
    },
    ...options,
  });
};

export const useDeleteFile = (organizationId: string, options?: UseMutationOptions<void, Error, string>) => {
  return useMutation({
    mutationFn: (fileId: string) => api.delete(API_ENDPOINTS.FILES.DELETE(organizationId, fileId)),
    ...options,
  });
};

// Utility hooks
export const useInvalidateQueries = () => {
  const queryClient = useQueryClient();
  
  return {
    invalidateAll: () => queryClient.invalidateQueries(),
    invalidateOrganization: (organizationId: string) => {
      queryClient.invalidateQueries({ queryKey: ['organizations', organizationId] });
    },
    invalidateStyles: (organizationId: string) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.style.list(organizationId) });
    },
    invalidateContent: (organizationId: string) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.content.list(organizationId) });
    },
  };
};
