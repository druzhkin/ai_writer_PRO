'use client';

// Content editor page with rich text editing, AI assistance, and version control

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useContentDetail } from '@/hooks/api';
import { useAuth } from '@/hooks/auth';
import { RichTextEditor } from '@/components/content/RichTextEditor';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Loading, SkeletonCard } from '@/components/ui/Loading';
import { cn, formatDateTime } from '@/lib/utils';
import {
  ArrowLeft,
  Save,
  Edit,
  Eye,
  Share,
  Download,
  Zap,
  FileText,
  Calendar,
  User,
  TrendingUp,
} from 'lucide-react';

const ContentEditorPage: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const contentId = params.id as string;
  
  const { organization } = useAuth();
  const { data: content, isLoading, error } = useContentDetail(
    organization?.id || '',
    contentId,
    { enabled: !!organization?.id }
  );

  const handleSave = (content: string) => {
    // TODO: Implement save functionality
    console.log('Saving content:', content);
  };

  const handleAIAssist = (prompt: string) => {
    // TODO: Implement AI assistance
    console.log('AI assist prompt:', prompt);
  };

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <SkeletonCard className="h-16" />
        <div className="grid gap-6 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <SkeletonCard className="h-96" />
          </div>
          <div>
            <SkeletonCard className="h-64" />
          </div>
        </div>
      </div>
    );
  }

  if (error || !content) {
    return (
      <div className="max-w-6xl mx-auto">
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Статья не найдена
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Запрашиваемая статья не существует или была удалена
          </p>
          <Button onClick={() => router.push('/dashboard/content')}>
            <ArrowLeft className="h-4 w-4 mr-2" />
            Вернуться к списку
          </Button>
        </div>
      </div>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'success';
      case 'edited':
        return 'info';
      case 'generated':
        return 'warning';
      default:
        return 'secondary';
    }
  };

  const getStatusText = (status: string) => {
    switch (status) {
      case 'published':
        return 'Опубликовано';
      case 'edited':
        return 'Отредактировано';
      case 'generated':
        return 'Сгенерировано';
      default:
        return 'Черновик';
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/dashboard/content')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {content.title}
            </h1>
            <div className="flex items-center space-x-4 mt-1">
              <Badge variant={getStatusColor(content.status)}>
                {getStatusText(content.status)}
              </Badge>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {formatDateTime(content.created_at)}
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm">
            <Eye className="h-4 w-4 mr-2" />
            Предпросмотр
          </Button>
          <Button variant="outline" size="sm">
            <Share className="h-4 w-4 mr-2" />
            Поделиться
          </Button>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Экспорт
          </Button>
          <Button size="sm">
            <Save className="h-4 w-4 mr-2" />
            Сохранить
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Editor */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Edit className="h-5 w-5" />
                <span>Редактор</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <RichTextEditor
                content={content.content}
                onChange={(newContent) => {
                  // TODO: Handle content change
                  console.log('Content changed:', newContent);
                }}
                onSave={handleSave}
                onAIAssist={handleAIAssist}
                placeholder="Начните редактировать статью..."
              />
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Article Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <FileText className="h-5 w-5" />
                <span>Информация</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Бриф
                </label>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {content.brief}
                </p>
              </div>
              
              {content.style_profile && (
                <div>
                  <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                    Стиль
                  </label>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                    {content.style_profile.name}
                  </p>
                </div>
              )}
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <label className="font-medium text-gray-700 dark:text-gray-300">
                    Токены
                  </label>
                  <p className="text-gray-600 dark:text-gray-400">
                    {content.token_count}
                  </p>
                </div>
                <div>
                  <label className="font-medium text-gray-700 dark:text-gray-300">
                    Стоимость
                  </label>
                  <p className="text-gray-600 dark:text-gray-400">
                    {content.cost.toFixed(4)} ₽
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* AI Assistant */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Zap className="h-5 w-5" />
                <span>ИИ-помощник</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => handleAIAssist('Улучшить текст')}
                >
                  <Zap className="h-4 w-4 mr-2" />
                  Улучшить текст
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => handleAIAssist('Исправить ошибки')}
                >
                  <Edit className="h-4 w-4 mr-2" />
                  Исправить ошибки
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  className="w-full"
                  onClick={() => handleAIAssist('Сократить текст')}
                >
                  <TrendingUp className="h-4 w-4 mr-2" />
                  Сократить текст
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Version History */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Calendar className="h-5 w-5" />
                <span>История версий</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {content.iterations?.slice(0, 3).map((iteration, index) => (
                  <div key={iteration.id} className="flex items-center space-x-3 p-2 rounded-md hover:bg-gray-50 dark:hover:bg-gray-800">
                    <div className="flex-shrink-0">
                      <div className="w-2 h-2 rounded-full bg-blue-500" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 dark:text-white">
                        Версия {content.iterations.length - index}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400">
                        {formatDateTime(iteration.created_at)}
                      </p>
                    </div>
                  </div>
                ))}
                {content.iterations && content.iterations.length > 3 && (
                  <Button variant="ghost" size="sm" className="w-full">
                    Показать все версии
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default ContentEditorPage;
