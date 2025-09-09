'use client';

// Style form component for creating and editing style profiles

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { FileUpload } from './FileUpload';
import { cn } from '@/lib/utils';
import { styleCreationSchema, StyleCreationFormData } from '@/types/forms';
import { useCreateStyle, useUpdateStyle, useUploadFile } from '@/hooks/api';
import { useAuth } from '@/hooks/auth';
import { Palette, Upload, AlertCircle } from 'lucide-react';

interface StyleFormProps {
  styleId?: string;
  initialData?: Partial<StyleCreationFormData>;
  onSuccess?: () => void;
  onCancel?: () => void;
  className?: string;
}

const StyleForm: React.FC<StyleFormProps> = ({
  styleId,
  initialData,
  onSuccess,
  onCancel,
  className,
}) => {
  const { organization } = useAuth();
  const isEditing = !!styleId;
  
  const createStyleMutation = useCreateStyle(organization?.id || '');
  const updateStyleMutation = useUpdateStyle(organization?.id || '', styleId || '');
  const uploadFileMutation = useUploadFile(organization?.id || '');

  const form = useForm<StyleCreationFormData>({
    resolver: zodResolver(styleCreationSchema),
    defaultValues: {
      name: initialData?.name || '',
      description: initialData?.description || '',
      reference_articles: initialData?.reference_articles || [],
    },
  });

  const { register, handleSubmit, formState: { errors }, watch, setValue } = form;
  const watchedFiles = watch('reference_articles');

  const onSubmit = async (data: StyleCreationFormData) => {
    try {
      if (isEditing) {
        await updateStyleMutation.mutateAsync({
          name: data.name,
          description: data.description,
        });
      } else {
        // Upload files first and collect IDs
        const fileIds: string[] = [];
        for (const file of data.reference_articles) {
          const uploadResult = await uploadFileMutation.mutateAsync(file);
          fileIds.push(uploadResult.file_id);
        }
        
        // Create style with file IDs
        await createStyleMutation.mutateAsync({
          name: data.name,
          description: data.description,
          reference_article_ids: fileIds,
        });
      }
      onSuccess?.();
    } catch (error) {
      console.error('Error saving style:', error);
    }
  };

  const handleFilesChange = (files: File[]) => {
    setValue('reference_articles', files, { shouldValidate: true });
  };

  const isLoading = createStyleMutation.isPending || updateStyleMutation.isPending || uploadFileMutation.isPending;
  const error = createStyleMutation.error || updateStyleMutation.error || uploadFileMutation.error;

  return (
    <div className={cn('max-w-2xl mx-auto', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Palette className="h-5 w-5" />
            <span>{isEditing ? 'Редактировать стиль' : 'Создать новый стиль'}</span>
          </CardTitle>
        </CardHeader>
        
        <CardContent>
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Error message */}
            {error && (
              <div className="rounded-md bg-red-50 dark:bg-red-900/20 p-4">
                <div className="flex">
                  <AlertCircle className="h-5 w-5 text-red-400" />
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800 dark:text-red-200">
                      Ошибка сохранения
                    </h3>
                    <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                      {error.message || 'Произошла ошибка при сохранении стиля'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Style name */}
            <Input
              {...register('name')}
              type="text"
              label="Название стиля"
              placeholder="Введите название стиля"
              error={errors.name?.message}
              required
            />

            {/* Style description */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Описание стиля
              </label>
              <textarea
                {...register('description')}
                rows={4}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Опишите особенности стиля письма..."
              />
              {errors.description && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {errors.description.message}
                </p>
              )}
            </div>

            {/* File upload */}
            {!isEditing && (
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Референсные статьи
                </label>
                <FileUpload
                  onFilesChange={handleFilesChange}
                  maxFiles={10}
                  acceptedTypes={['text/plain', 'application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']}
                />
                {errors.reference_articles && (
                  <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                    {errors.reference_articles.message}
                  </p>
                )}
                
                {watchedFiles && watchedFiles.length > 0 && (
                  <div className="mt-3">
                    <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                      Загружено файлов: {watchedFiles.length}
                    </p>
                    <div className="space-y-1">
                      {watchedFiles.map((file, index) => (
                        <div key={index} className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
                          <Upload className="h-4 w-4" />
                          <span className="truncate">{file.name}</span>
                          <span className="text-gray-400">
                            ({(file.size / 1024 / 1024).toFixed(2)} MB)
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Form actions */}
            <div className="flex items-center justify-end space-x-3 pt-6 border-t border-gray-200 dark:border-gray-700">
              {onCancel && (
                <Button
                  type="button"
                  variant="outline"
                  onClick={onCancel}
                  disabled={isLoading}
                >
                  Отмена
                </Button>
              )}
              
              <Button
                type="submit"
                loading={isLoading}
                disabled={isLoading}
              >
                {isEditing ? 'Сохранить изменения' : 'Создать стиль'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export { StyleForm };
