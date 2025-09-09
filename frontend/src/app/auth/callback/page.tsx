'use client';

// OAuth callback page for handling Google and GitHub authentication responses

import React, { useEffect } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { useOAuthCallback } from '@/hooks/auth';
import { Loading } from '@/components/ui/Loading';

const OAuthCallbackPage: React.FC = () => {
  const searchParams = useSearchParams();
  const router = useRouter();
  const { handleCallback, isLoading, error, clearError } = useOAuthCallback();

  useEffect(() => {
    const code = searchParams.get('code');
    const state = searchParams.get('state');
    const provider = searchParams.get('provider') as 'google' | 'github';

    if (code && state && provider) {
      handleCallback(code, state, provider);
    } else {
      // Invalid callback parameters
      router.push('/login?error=invalid_callback');
    }
  }, [searchParams, handleCallback, router]);

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-red-600 mb-4">
            Ошибка авторизации
          </h2>
          <p className="text-gray-600 mb-4">{error}</p>
          <button
            onClick={() => {
              clearError();
              router.push('/login');
            }}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
          >
            Вернуться к входу
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <Loading text="Завершение авторизации..." />
        <p className="mt-4 text-gray-600">
          Перенаправляем вас в систему...
        </p>
      </div>
    </div>
  );
};

export default OAuthCallbackPage;
