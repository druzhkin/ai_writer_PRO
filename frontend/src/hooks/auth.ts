// Custom hooks for authentication state, form handling, and UI interactions

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuthStore } from '@/store/auth';
import { authService } from '@/lib/auth';
import {
  loginSchema,
  registerSchema,
  passwordResetSchema,
  passwordResetConfirmSchema,
  LoginFormData,
  RegisterFormData,
  PasswordResetFormData,
  PasswordResetConfirmFormData,
} from '@/types/forms';

// Authentication state hook
export const useAuth = () => {
  const {
    user,
    organization,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    clearError,
    initialize,
  } = useAuthStore();

  // Initialize auth state on mount
  useEffect(() => {
    initialize();
  }, [initialize]);

  return {
    user,
    organization,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    clearError,
  };
};

// Protected route hook
export const useProtectedRoute = (redirectTo: string = '/login') => {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (!isLoading) {
      if (!isAuthenticated) {
        router.push(redirectTo);
      } else {
        setIsChecking(false);
      }
    }
  }, [isAuthenticated, isLoading, router, redirectTo]);

  return { isAuthenticated, isLoading: isLoading || isChecking };
};

// Public route hook (redirect if authenticated)
export const usePublicRoute = (redirectTo: string = '/dashboard') => {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const [isChecking, setIsChecking] = useState(true);

  useEffect(() => {
    if (!isLoading) {
      if (isAuthenticated) {
        router.push(redirectTo);
      } else {
        setIsChecking(false);
      }
    }
  }, [isAuthenticated, isLoading, router, redirectTo]);

  return { isAuthenticated, isLoading: isLoading || isChecking };
};

// Login form hook
export const useLoginForm = () => {
  const { login, isLoading, error, clearError } = useAuth();
  const router = useRouter();

  const form = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  const onSubmit = useCallback(async (data: LoginFormData) => {
    try {
      clearError();
      await login(data.email, data.password);
      router.push('/dashboard');
    } catch (error) {
      // Error is handled by the store
    }
  }, [login, clearError, router]);

  return {
    form,
    onSubmit: form.handleSubmit(onSubmit),
    isLoading,
    error,
    clearError,
  };
};

// Register form hook
export const useRegisterForm = () => {
  const { register: registerUser, isLoading, error, clearError } = useAuth();
  const router = useRouter();

  const form = useForm<RegisterFormData>({
    resolver: zodResolver(registerSchema),
    defaultValues: {
      email: '',
      password: '',
      confirmPassword: '',
      full_name: '',
      organization_name: '',
    },
  });

  const onSubmit = useCallback(async (data: RegisterFormData) => {
    try {
      clearError();
      await registerUser({
        email: data.email,
        password: data.password,
        full_name: data.full_name,
        organization_name: data.organization_name,
      });
      router.push('/login?registered=true');
    } catch (error) {
      // Error is handled by the store
    }
  }, [registerUser, clearError, router]);

  return {
    form,
    onSubmit: form.handleSubmit(onSubmit),
    isLoading,
    error,
    clearError,
  };
};

// Password reset form hook
export const usePasswordResetForm = () => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const form = useForm<PasswordResetFormData>({
    resolver: zodResolver(passwordResetSchema),
    defaultValues: {
      email: '',
    },
  });

  const onSubmit = useCallback(async (data: PasswordResetFormData) => {
    try {
      setIsLoading(true);
      setError(null);
      await authService.requestPasswordReset(data.email);
      setIsSubmitted(true);
    } catch (error: any) {
      setError(error.detail || 'Ошибка отправки запроса на сброс пароля');
    } finally {
      setIsLoading(false);
    }
  }, []);

  return {
    form,
    onSubmit: form.handleSubmit(onSubmit),
    isLoading,
    error,
    isSubmitted,
    clearError: () => setError(null),
  };
};

// Password reset confirm form hook
export const usePasswordResetConfirmForm = (token: string) => {
  const [isSubmitted, setIsSubmitted] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const form = useForm<PasswordResetConfirmFormData>({
    resolver: zodResolver(passwordResetConfirmSchema),
    defaultValues: {
      token,
      new_password: '',
      confirm_password: '',
    },
  });

  const onSubmit = useCallback(async (data: PasswordResetConfirmFormData) => {
    try {
      setIsLoading(true);
      setError(null);
      await authService.confirmPasswordReset(data.token, data.new_password);
      setIsSubmitted(true);
      setTimeout(() => {
        router.push('/login?passwordReset=true');
      }, 2000);
    } catch (error: any) {
      setError(error.detail || 'Ошибка сброса пароля');
    } finally {
      setIsLoading(false);
    }
  }, [token, router]);

  return {
    form,
    onSubmit: form.handleSubmit(onSubmit),
    isLoading,
    error,
    isSubmitted,
    clearError: () => setError(null),
  };
};

// OAuth login hook
export const useOAuthLogin = () => {
  const [isLoading, setIsLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const loginWithOAuth = useCallback(async (provider: 'google' | 'github') => {
    try {
      setIsLoading(provider);
      setError(null);
      const authUrl = await authService.oauthLogin(provider);
      window.location.href = authUrl;
    } catch (error: any) {
      setError(error.detail || `Ошибка входа через ${provider}`);
      setIsLoading(null);
    }
  }, []);

  return {
    loginWithOAuth,
    isLoading,
    error,
    clearError: () => setError(null),
  };
};

// OAuth callback hook
export const useOAuthCallback = () => {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const handleCallback = useCallback(async (code: string, state: string, provider: 'google' | 'github') => {
    try {
      setIsLoading(true);
      setError(null);
      await authService.oauthCallback(code, state, provider);
      router.push('/dashboard');
    } catch (error: any) {
      setError(error.detail || `Ошибка авторизации через ${provider}`);
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  return {
    handleCallback,
    isLoading,
    error,
    clearError: () => setError(null),
  };
};

// User profile hook
export const useUserProfile = () => {
  const { user, updateUser, isLoading, error, clearError } = useAuthStore();

  const updateProfile = useCallback(async (userData: Partial<typeof user>) => {
    try {
      clearError();
      await updateUser(userData);
    } catch (error) {
      // Error is handled by the store
    }
  }, [updateUser, clearError]);

  return {
    user,
    updateProfile,
    isLoading,
    error,
    clearError,
  };
};

// Logout hook
export const useLogout = () => {
  const { logout, isLoading } = useAuth();
  const router = useRouter();

  const handleLogout = useCallback(async () => {
    try {
      await logout();
      router.push('/login');
    } catch (error) {
      // Even if logout fails, redirect to login
      router.push('/login');
    }
  }, [logout, router]);

  return {
    logout: handleLogout,
    isLoading,
  };
};

// Organization context hook
export const useOrganizationContext = () => {
  const { organization } = useAuth();
  const { setOrganization } = useAuthStore();

  const switchOrganization = useCallback((newOrganization: typeof organization) => {
    if (newOrganization) {
      setOrganization(newOrganization);
    }
  }, [setOrganization]);

  return {
    currentOrganization: organization,
    switchOrganization,
  };
};

// Auto-refresh token hook
export const useAutoRefreshToken = () => {
  const { isAuthenticated } = useAuth();
  const [isRefreshing, setIsRefreshing] = useState(false);

  useEffect(() => {
    if (!isAuthenticated) return;

    const checkAndRefreshToken = async () => {
      if (authService.shouldRefreshToken()) {
        setIsRefreshing(true);
        try {
          await authService.refreshToken();
        } catch (error) {
          console.error('Auto token refresh failed:', error);
        } finally {
          setIsRefreshing(false);
        }
      }
    };

    // Check immediately
    checkAndRefreshToken();

    // Check every 5 minutes
    const interval = setInterval(checkAndRefreshToken, 5 * 60 * 1000);

    return () => clearInterval(interval);
  }, [isAuthenticated]);

  return { isRefreshing };
};
