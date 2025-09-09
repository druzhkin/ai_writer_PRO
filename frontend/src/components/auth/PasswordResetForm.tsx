'use client';

// Password reset form component with email input and reset confirmation handling

import React from 'react';
import Link from 'next/link';
import { usePasswordResetForm } from '@/hooks/auth';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { CheckCircle, ArrowLeft } from 'lucide-react';

const PasswordResetForm: React.FC = () => {
  const { form, onSubmit, isLoading, error, isSubmitted, clearError } = usePasswordResetForm();

  const { register, formState: { errors } } = form;

  if (isSubmitted) {
    return (
      <div className="space-y-6">
        <div className="text-center">
          <CheckCircle className="mx-auto h-12 w-12 text-green-500" />
          <h3 className="mt-4 text-lg font-medium text-gray-900 dark:text-white">
            Проверьте вашу почту
          </h3>
          <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
            Мы отправили инструкции по сбросу пароля на указанный email адрес.
          </p>
        </div>

        <div className="space-y-4">
          <div className="rounded-md bg-blue-50 dark:bg-blue-900/20 p-4">
            <div className="flex">
              <div className="ml-3">
                <h3 className="text-sm font-medium text-blue-800 dark:text-blue-200">
                  Что дальше?
                </h3>
                <div className="mt-2 text-sm text-blue-700 dark:text-blue-300">
                  <ul className="list-disc list-inside space-y-1">
                    <li>Проверьте папку "Входящие" в вашем email</li>
                    <li>Если письма нет, проверьте папку "Спам"</li>
                    <li>Перейдите по ссылке в письме для сброса пароля</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          <div className="flex flex-col space-y-3">
            <Link href="/login">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Вернуться к входу
              </Button>
            </Link>
            
            <button
              onClick={() => window.location.reload()}
              className="text-sm text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
            >
              Отправить письмо повторно
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error message */}
      {error && (
        <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                Ошибка
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

      {/* Instructions */}
      <div className="text-center">
        <h3 className="text-lg font-medium text-gray-900 dark:text-white">
          Сброс пароля
        </h3>
        <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
          Введите ваш email адрес, и мы отправим вам инструкции по сбросу пароля.
        </p>
      </div>

      {/* Reset form */}
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

        <Button
          type="submit"
          className="w-full"
          loading={isLoading}
          disabled={isLoading}
        >
          Отправить инструкции
        </Button>
      </form>

      {/* Back to login */}
      <div className="text-center">
        <Link
          href="/login"
          className="inline-flex items-center text-sm text-blue-600 hover:text-blue-500 dark:text-blue-400 dark:hover:text-blue-300"
        >
          <ArrowLeft className="h-4 w-4 mr-1" />
          Вернуться к входу
        </Link>
      </div>
    </div>
  );
};

export { PasswordResetForm };
