'use client';

// Login page with authentication form and OAuth options

import React from 'react';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { LoginForm } from '@/components/auth/LoginForm';
import { usePublicRoute } from '@/hooks/auth';

const LoginPage: React.FC = () => {
  const { isLoading } = usePublicRoute();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <AuthLayout
      title="Вход в систему"
      subtitle="Войдите в свой аккаунт для продолжения работы"
    >
      <LoginForm />
    </AuthLayout>
  );
};

export default LoginPage;
