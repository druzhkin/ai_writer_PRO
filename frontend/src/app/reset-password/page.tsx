'use client';

// Password reset page with email input and reset confirmation handling

import React from 'react';
import { AuthLayout } from '@/components/layout/AuthLayout';
import { PasswordResetForm } from '@/components/auth/PasswordResetForm';
import { usePublicRoute } from '@/hooks/auth';

const ResetPasswordPage: React.FC = () => {
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
      title="Сброс пароля"
      subtitle="Введите ваш email для получения инструкций по сбросу пароля"
    >
      <PasswordResetForm />
    </AuthLayout>
  );
};

export default ResetPasswordPage;
