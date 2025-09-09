'use client';

// Registration page with user signup form and organization creation

import React from 'react';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { RegisterForm } from '@/components/auth/RegisterForm';
import { usePublicRoute } from '@/hooks/auth';

const RegisterPage: React.FC = () => {
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
      title="Создать аккаунт"
      subtitle="Зарегистрируйтесь для начала работы с AI Writer Pro"
    >
      <RegisterForm />
    </AuthLayout>
  );
};

export default RegisterPage;
