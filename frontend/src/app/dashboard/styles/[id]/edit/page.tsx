'use client';

// Style edit page with form for updating style details

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useStyle } from '@/hooks/api';
import { useAuth } from '@/hooks/auth';
import { StyleForm } from '@/components/styles/StyleForm';
import { Loading, SkeletonCard } from '@/components/ui/Loading';
import { ArrowLeft } from 'lucide-react';
import { Button } from '@/components/ui/Button';

const StyleEditPage: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const styleId = params.id as string;
  
  const { organization } = useAuth();
  const { data: style, isLoading, error } = useStyle(
    organization?.id || '',
    styleId,
    { enabled: !!organization?.id }
  );

  const handleSuccess = () => {
    router.push(`/dashboard/styles/${styleId}`);
  };

  const handleCancel = () => {
    router.push(`/dashboard/styles/${styleId}`);
  };

  if (isLoading) {
    return (
      <div className="max-w-4xl mx-auto space-y-6">
        <SkeletonCard className="h-16" />
        <SkeletonCard className="h-96" />
      </div>
    );
  }

  if (error || !style) {
    return (
      <div className="max-w-4xl mx-auto">
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Стиль не найден
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Запрашиваемый стиль не существует или был удален
          </p>
          <Button onClick={() => router.push('/dashboard/styles')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Вернуться к списку
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center space-x-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push(`/dashboard/styles/${styleId}`)}
        >
          <ArrowLeft className="h-4 w-4" />
        </Button>
        
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Редактировать стиль
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Обновите информацию о стиле письма
          </p>
        </div>
      </div>

      {/* Edit Form */}
      <StyleForm
        styleId={styleId}
        initialData={{
          name: style.name,
          description: style.description || '',
        }}
        onSuccess={handleSuccess}
        onCancel={handleCancel}
      />
    </div>
  );
};

export default StyleEditPage;
