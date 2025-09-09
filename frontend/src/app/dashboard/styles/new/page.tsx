// New style creation page with form for style details and reference article upload

import React from 'react';
import { useRouter } from 'next/navigation';
import { StyleForm } from '@/components/styles/StyleForm';

const NewStylePage: React.FC = () => {
  const router = useRouter();

  const handleSuccess = () => {
    router.push('/dashboard/styles');
  };

  const handleCancel = () => {
    router.push('/dashboard/styles');
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          Создать новый стиль
        </h1>
        <p className="text-gray-600 dark:text-gray-400">
          Создайте стиль письма на основе референсных материалов
        </p>
      </div>
      
      <StyleForm
        onSuccess={handleSuccess}
        onCancel={handleCancel}
      />
    </div>
  );
};

export default NewStylePage;
