'use client';

// Login form component with email/password authentication and OAuth buttons

import React from 'react';
import Link from 'next/link';
import { useLoginForm, useOAuthLogin } from '@/hooks/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { OAuthButtons } from './OAuthButtons';
import { Eye, EyeOff } from 'lucide-react';

const LoginForm: React.FC = () => {
  const { form, onSubmit, isLoading, error, clearError } = useLoginForm();
  const { loginWithOAuth, isLoading: oauthLoading } = useOAuthLogin();
  const [showPassword, setShowPassword] = React.useState(false);

  const { register, formState: { errors } } = form;

  return (
    <div className="space-y-6">
      {/* Error message */}
      {error && (
        <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                Ошибка входа
              </h3>
              <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                {error}
              </div>
              <div className="mt-4">
                <button
                  type="button"
                  onClick={clearError}
                  className="text-sm font-medium text-red-800 dark:text-red-200 hover:text-red-600 dark:hover:text-red-400"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* OAuth buttons */}
      <div className="space-y-3">
        <OAuthButtons 
          onGoogleLogin={() => loginWithOAuth('google')}
          onGitHubLogin={() => loginWithOAuth('github')}
          isLoading={oauthLoading}
        />
        
        <div className="relative">
          <div className="absolute inset-0 flex items-center">
            <div className="w-full border-t border-gray-300 dark:border-gray-600" />
          </div>
          <div className="relative flex justify-center text-sm">
            <span className="px-2 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400">
              или войдите с помощью email
            </span>
          </div>
        </div>
      </div>

      {/* Login form */}
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          {...register('email')}
          type="email"
          label="Email"
          placeholder="Введите ваш email"
          error={errors.email?.message}
          autoComplete="email"
          required
        />

        <div className="relative">
          <Input
            {...register('password')}
            type={showPassword ? 'text' : 'password'}
            label="Пароль"
            placeholder="Введите ваш пароль"
            error={errors.password?.message}
            autoComplete="current-password"
            required
            rightIcon={
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            }
          />
        </div>

        <div className="flex items-center justify-between">
          <div className="flex items-center">
            <input
              id="remember-me"
              name="remember-me"
              type="checkbox"
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
            <label htmlFor="remember-me" className="ml-2 block text-sm text-gray-900 dark:text-gray-300">
              Запомнить меня
            </label>
          </div>

          <div className="text-sm">
            <Link
              href="/reset-password"
              className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
            >
              Забыли пароль?
            </Link>
          </div>
        </div>

        <Button
          type="submit"
          className="w-full"
          loading={isLoading}
          disabled={isLoading}
        >
          Войти
        </Button>
      </form>

      {/* Sign up link */}
      <div className="text-center">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Нет аккаунта?{' '}
          <Link
            href="/register"
            className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Зарегистрироваться
          </Link>
        </p>
      </div>
    </div>
  );
};

export { LoginForm };
