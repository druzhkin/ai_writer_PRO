'use client';

// Content generation form component with style selection and generation parameters

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { cn } from '@/lib/utils';
import { contentGenerationSchema, ContentGenerationFormData } from '@/types/forms';
import { useGenerateContent, useStyles } from '@/hooks/api';
import { useAuth } from '@/hooks/auth';
import { 
  FileText, 
  Palette, 
  Settings, 
  Zap, 
  AlertCircle,
  Info,
  Clock,
  DollarSign,
} from 'lucide-react';

interface ContentGenerationFormProps {
  onSuccess?: (content: any) => void;
  onCancel?: () => void;
  className?: string;
}

const ContentGenerationForm: React.FC<ContentGenerationFormProps> = ({
  onSuccess,
  onCancel,
  className,
}) => {
  const { organization } = useAuth();
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  const generateContentMutation = useGenerateContent(organization?.id || '');
  const { data: styles } = useStyles(organization?.id || '', { is_active: true });

  const form = useForm<ContentGenerationFormData>({
    resolver: zodResolver(contentGenerationSchema),
    defaultValues: {
      brief: '',
      style_profile_id: '',
      max_tokens: 2000,
      temperature: 0.7,
      additional_instructions: '',
    },
  });

  const { register, handleSubmit, formState: { errors }, watch } = form;
  const watchedTokens = watch('max_tokens');
  const watchedTemperature = watch('temperature');

  // Calculate estimated cost (rough estimate)
  const estimatedCost = (watchedTokens || 2000) * 0.00002; // $0.00002 per token

  const onSubmit = async (data: ContentGenerationFormData) => {
    try {
      const result = await generateContentMutation.mutateAsync(data);
      onSuccess?.(result.content);
    } catch (error) {
      console.error('Error generating content:', error);
    }
  };

  const isLoading = generateContentMutation.isPending;
  const error = generateContentMutation.error;

  return (
    <div className={cn('max-w-4xl mx-auto', className)}>
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5" />
            <span>Генерация контента</span>
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
                      Ошибка генерации
                    </h3>
                    <div className="mt-2 text-sm text-red-700 dark:text-red-300">
                      {error.message || 'Произошла ошибка при генерации контента'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Brief */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Бриф для статьи *
              </label>
              <textarea
                {...register('brief')}
                rows={6}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Опишите, какую статью вы хотите создать. Укажите тему, целевую аудиторию, ключевые моменты, которые нужно раскрыть..."
                required
              />
              {errors.brief && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {errors.brief.message}
                </p>
              )}
              <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                Чем подробнее бриф, тем лучше результат
              </p>
            </div>

            {/* Style selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Стиль письма *
              </label>
              {styles && styles.length > 0 ? (
                <div className="grid gap-3 md:grid-cols-2">
                  {styles.map((style) => (
                    <label
                      key={style.id}
                      className="relative flex items-start space-x-3 p-3 border border-gray-200 dark:border-gray-600 rounded-lg cursor-pointer hover:bg-gray-50 dark:hover:bg-gray-800"
                    >
                      <input
                        {...register('style_profile_id')}
                        type="radio"
                        value={style.id}
                        className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300"
                      />
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center space-x-2">
                          <Palette className="h-4 w-4 text-blue-500" />
                          <span className="text-sm font-medium text-gray-900 dark:text-white">
                            {style.name}
                          </span>
                        </div>
                        {style.description && (
                          <p className="mt-1 text-xs text-gray-600 dark:text-gray-400 line-clamp-2">
                            {style.description}
                          </p>
                        )}
                        <div className="mt-2 flex items-center space-x-2">
                          <Badge variant="info" className="text-xs">
                            {style.reference_articles?.length || 0} референсов
                          </Badge>
                          {style.analysis_result && (
                            <Badge variant="success" className="text-xs">
                              Проанализирован
                            </Badge>
                          )}
                        </div>
                      </div>
                    </label>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 border border-gray-200 dark:border-gray-600 rounded-lg">
                  <Palette className="mx-auto h-8 w-8 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    Нет доступных стилей
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-500">
                    Создайте стиль письма для генерации контента
                  </p>
                </div>
              )}
              {errors.style_profile_id && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {errors.style_profile_id.message}
                </p>
              )}
            </div>

            {/* Additional instructions */}
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                Дополнительные инструкции
              </label>
              <textarea
                {...register('additional_instructions')}
                rows={3}
                className="w-full rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 px-3 py-2 text-sm placeholder-gray-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                placeholder="Дополнительные требования к статье, структуре, тону..."
              />
              {errors.additional_instructions && (
                <p className="mt-1 text-sm text-red-600 dark:text-red-400">
                  {errors.additional_instructions.message}
                </p>
              )}
            </div>

            {/* Advanced settings toggle */}
            <div className="border-t border-gray-200 dark:border-gray-700 pt-6">
              <button
                type="button"
                onClick={() => setShowAdvanced(!showAdvanced)}
                className="flex items-center space-x-2 text-sm font-medium text-gray-700 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
              >
                <Settings className="h-4 w-4" />
                <span>Дополнительные настройки</span>
              </button>
            </div>

            {/* Advanced settings */}
            {showAdvanced && (
              <div className="space-y-4 p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
                <div className="grid gap-4 md:grid-cols-2">
                  {/* Max tokens */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Максимум токенов
                    </label>
                    <Input
                      {...register('max_tokens', { valueAsNumber: true })}
                      type="number"
                      min={100}
                      max={4000}
                      step={100}
                      error={errors.max_tokens?.message}
                    />
                    <p className="mt-1 text-xs text-gray-500 dark:text-gray-400">
                      Больше токенов = более длинная статья
                    </p>
                  </div>

                  {/* Temperature */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                      Креативность: {watchedTemperature}
                    </label>
                    <input
                      {...register('temperature', { valueAsNumber: true })}
                      type="range"
                      min={0}
                      max={2}
                      step={0.1}
                      className="w-full h-2 bg-gray-200 dark:bg-gray-700 rounded-lg appearance-none cursor-pointer"
                    />
                    <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mt-1">
                      <span>Точный</span>
                      <span>Сбалансированный</span>
                      <span>Креативный</span>
                    </div>
                  </div>
                </div>

                {/* Cost estimation */}
                <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="flex items-center space-x-2">
                    <Info className="h-4 w-4 text-blue-500" />
                    <span className="text-sm text-blue-700 dark:text-blue-300">
                      Примерная стоимость
                    </span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm">
                    <div className="flex items-center space-x-1">
                      <Clock className="h-4 w-4 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-400">
                        ~{Math.ceil((watchedTokens || 2000) / 1000)} мин
                      </span>
                    </div>
                    <div className="flex items-center space-x-1">
                      <DollarSign className="h-4 w-4 text-gray-500" />
                      <span className="text-gray-600 dark:text-gray-400">
                        ~{estimatedCost.toFixed(4)} ₽
                      </span>
                    </div>
                  </div>
                </div>
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
                disabled={isLoading || !styles?.length}
                className="min-w-32"
              >
                <Zap className="h-4 w-4 mr-2" />
                {isLoading ? 'Генерируем...' : 'Создать статью'}
              </Button>
            </div>
          </form>
        </CardContent>
      </Card>
    </div>
  );
};

export { ContentGenerationForm };
