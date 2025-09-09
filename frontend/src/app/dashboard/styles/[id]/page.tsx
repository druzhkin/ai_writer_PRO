'use client';

// Style detail page with analysis display and reference management

import React from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useStyle, useStyleAnalysis } from '@/hooks/api';
import { useAuth } from '@/hooks/auth';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Loading, SkeletonCard } from '@/components/ui/Loading';
import { cn, formatDateTime } from '@/lib/utils';
import {
  ArrowLeft,
  Edit,
  Palette,
  FileText,
  Calendar,
  User,
  TrendingUp,
  Target,
  MessageSquare,
  BookOpen,
} from 'lucide-react';

const StyleDetailPage: React.FC = () => {
  const params = useParams();
  const router = useRouter();
  const styleId = params.id as string;
  
  const { organization } = useAuth();
  const { data: style, isLoading, error } = useStyle(
    organization?.id || '',
    styleId,
    { enabled: !!organization?.id }
  );
  
  const { data: analysis } = useStyleAnalysis(
    organization?.id || '',
    styleId,
    { enabled: !!organization?.id && !!style }
  );

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

  if (error || !style) {
    return (
      <div className="max-w-6xl mx-auto">
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
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => router.push('/dashboard/styles')}
          >
            <ArrowLeft className="h-4 w-4" />
          </Button>
          
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              {style.name}
            </h1>
            <div className="flex items-center space-x-4 mt-1">
              <Badge variant={style.is_active ? 'success' : 'secondary'}>
                {style.is_active ? 'Активен' : 'Неактивен'}
              </Badge>
              <span className="text-sm text-gray-500 dark:text-gray-400">
                {formatDateTime(style.created_at)}
              </span>
            </div>
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => router.push(`/dashboard/styles/${style.id}/edit`)}
          >
            <Edit className="h-4 w-4 mr-2" />
            Редактировать
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Main Content */}
        <div className="lg:col-span-2 space-y-6">
          {/* Description */}
          {style.description && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MessageSquare className="h-5 w-5" />
                  <span>Описание</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-gray-600 dark:text-gray-400">
                  {style.description}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Style Analysis */}
          {analysis && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <TrendingUp className="h-5 w-5" />
                  <span>Анализ стиля</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 md:grid-cols-2">
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Тон
                    </label>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {analysis.analysis.tone}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Голос
                    </label>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {analysis.analysis.voice}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Структура
                    </label>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {analysis.analysis.structure}
                    </p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Длина предложений
                    </label>
                    <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                      {analysis.analysis.sentence_length}
                    </p>
                  </div>
                </div>
                
                {analysis.analysis.vocabulary && analysis.analysis.vocabulary.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Ключевые слова
                    </label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {analysis.analysis.vocabulary.map((word, index) => (
                        <Badge key={index} variant="outline">
                          {word}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
                
                {analysis.analysis.key_phrases && analysis.analysis.key_phrases.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                      Ключевые фразы
                    </label>
                    <div className="flex flex-wrap gap-2 mt-2">
                      {analysis.analysis.key_phrases.map((phrase, index) => (
                        <Badge key={index} variant="secondary">
                          {phrase}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}

          {/* Reference Articles */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <BookOpen className="h-5 w-5" />
                <span>Референсные статьи</span>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {style.reference_articles && style.reference_articles.length > 0 ? (
                <div className="space-y-3">
                  {style.reference_articles.map((article) => (
                    <div key={article.id} className="flex items-center space-x-3 p-3 border border-gray-200 dark:border-gray-700 rounded-lg">
                      <FileText className="h-4 w-4 text-gray-400" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                          {article.title}
                        </p>
                        <p className="text-xs text-gray-500 dark:text-gray-400">
                          {article.file_type} • {(article.file_size / 1024).toFixed(1)} KB
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <FileText className="mx-auto h-8 w-8 text-gray-400" />
                  <p className="mt-2 text-sm text-gray-600 dark:text-gray-400">
                    Нет референсных статей
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Style Info */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2">
                <Palette className="h-5 w-5" />
                <span>Информация</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Статус
                </label>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {style.is_active ? 'Активен' : 'Неактивен'}
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Референсных статей
                </label>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {style.reference_articles?.length || 0}
                </p>
              </div>
              
              <div>
                <label className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  Анализ
                </label>
                <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
                  {analysis ? 'Завершен' : 'В процессе'}
                </p>
              </div>
              
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <label className="font-medium text-gray-700 dark:text-gray-300">
                    Создан
                  </label>
                  <p className="text-gray-600 dark:text-gray-400">
                    {formatDateTime(style.created_at)}
                  </p>
                </div>
                <div>
                  <label className="font-medium text-gray-700 dark:text-gray-300">
                    Обновлен
                  </label>
                  <p className="text-gray-600 dark:text-gray-400">
                    {formatDateTime(style.updated_at)}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Confidence Score */}
          {analysis && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Target className="h-5 w-5" />
                  <span>Уверенность анализа</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600 dark:text-gray-400">
                      Точность
                    </span>
                    <span className="text-sm font-medium">
                      {Math.round(analysis.analysis.confidence_score * 100)}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300" 
                      style={{ width: `${analysis.analysis.confidence_score * 100}%` }}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default StyleDetailPage;
