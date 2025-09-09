// New content generation page with style selection, brief input, and generation parameters

import React from 'react';
import { useRouter } from 'next/navigation';
import { ContentGenerationForm } from '@/components/content/ContentGenerationForm';

const NewContentPage: React.FC = () => {
  const router = useRouter();

  const handleSuccess = (content: any) => {
    router.push(`/dashboard/content/${content.id}`);
  };

  const handleCancel = () => {
    router.push('/dashboard/content');
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Создать новую статью
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Сгенерируйте статью с помощью ИИ на основе вашего брифа и стиля
        </p>
      </div>
      
      <ContentGenerationForm
        onSuccess={handleSuccess}
        onCancel={handleCancel}
      />
    </div>
  );
};

export default NewContentPage;
