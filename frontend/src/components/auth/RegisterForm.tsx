'use client';

// Registration form component with user details and organization creation

import React from 'react';
import Link from 'next/link';
import { useRegisterForm, useOAuthLogin } from '@/hooks/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { OAuthButtons } from './OAuthButtons';
import { Eye, EyeOff, CheckCircle } from 'lucide-react';

const RegisterForm: React.FC = () => {
  const { form, onSubmit, isLoading, error, clearError } = useRegisterForm();
  const { loginWithOAuth, isLoading: oauthLoading } = useOAuthLogin();
  const [showPassword, setShowPassword] = React.useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = React.useState(false);

  const { register, formState: { errors }, watch } = form;
  const password = watch('password');

  // Password strength indicator
  const getPasswordStrength = (password: string) => {
    if (!password) return { score: 0, label: '', color: '' };
    
    let score = 0;
    if (password.length >= 8) score++;
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/\d/.test(password)) score++;
    if (/[^A-Za-z0-9]/.test(password)) score++;

    const strength = [
      { score: 0, label: 'Очень слабый', color: 'bg-red-500' },
      { score: 1, label: 'Слабый', color: 'bg-red-400' },
      { score: 2, label: 'Средний', color: 'bg-yellow-500' },
      { score: 3, label: 'Хороший', color: 'bg-blue-500' },
      { score: 4, label: 'Отличный', color: 'bg-green-500' },
      { score: 5, label: 'Отличный', color: 'bg-green-500' },
    ];

    return strength[Math.min(score, 5)];
  };

  const passwordStrength = getPasswordStrength(password || '');

  return (
    <div className="space-y-6">
      {/* Error message */}
      {error && (
        <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                Ошибка регистрации
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
              или зарегистрируйтесь с помощью email
            </span>
          </div>
        </div>
      </div>

      {/* Registration form */}
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          <Input
            {...register('full_name')}
            type="text"
            label="Полное имя"
            placeholder="Введите ваше имя"
            error={errors.full_name?.message}
            autoComplete="name"
            required
          />
          
          <Input
            {...register('email')}
            type="email"
            label="Email"
            placeholder="Введите ваш email"
            error={errors.email?.message}
            autoComplete="email"
            required
          />
        </div>

        <Input
          {...register('organization_name')}
          type="text"
          label="Название организации"
          placeholder="Введите название вашей организации"
          error={errors.organization_name?.message}
          autoComplete="organization"
          required
        />

        <div className="relative">
          <Input
            {...register('password')}
            type={showPassword ? 'text' : 'password'}
            label="Пароль"
            placeholder="Создайте пароль"
            error={errors.password?.message}
            autoComplete="new-password"
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
          
          {/* Password strength indicator */}
          {password && (
            <div className="mt-2">
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-300 ${passwordStrength.color}`}
                    style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500 dark:text-gray-400">
                  {passwordStrength.label}
                </span>
              </div>
            </div>
          )}
        </div>

        <div className="relative">
          <Input
            {...register('confirmPassword')}
            type={showConfirmPassword ? 'text' : 'password'}
            label="Подтвердите пароль"
            placeholder="Повторите пароль"
            error={errors.confirmPassword?.message}
            autoComplete="new-password"
            required
            rightIcon={
              <button
                type="button"
                onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
              >
                {showConfirmPassword ? (
                  <EyeOff className="h-4 w-4" />
                ) : (
                  <Eye className="h-4 w-4" />
                )}
              </button>
            }
          />
        </div>

        {/* Terms and conditions */}
        <div className="flex items-start">
          <div className="flex items-center h-5">
            <input
              id="terms"
              name="terms"
              type="checkbox"
              required
              className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
            />
          </div>
          <div className="ml-3 text-sm">
            <label htmlFor="terms" className="text-gray-700 dark:text-gray-300">
              Я согласен с{' '}
              <Link href="/terms" className="text-blue-600 hover:text-blue-500 dark:text-blue-400">
                условиями использования
              </Link>{' '}
              и{' '}
              <Link href="/privacy" className="text-blue-600 hover:text-blue-500 dark:text-blue-400">
                политикой конфиденциальности
              </Link>
            </label>
          </div>
        </div>

        <Button
          type="submit"
          className="w-full"
          loading={isLoading}
          disabled={isLoading}
        >
          Создать аккаунт
        </Button>
      </form>

      {/* Sign in link */}
      <div className="text-center">
        <p className="text-sm text-gray-600 dark:text-gray-400">
          Уже есть аккаунт?{' '}
          <Link
            href="/login"
            className="font-medium text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
          >
            Войти
          </Link>
        </p>
      </div>
    </div>
  );
};

export { RegisterForm };
