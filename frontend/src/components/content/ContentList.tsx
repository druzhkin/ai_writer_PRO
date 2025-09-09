'use client';

// Content list component for displaying generated content with search and filtering

import React, { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Loading, SkeletonCard } from '@/components/ui/Loading';
import { cn, formatDateTime, truncateText } from '@/lib/utils';
import { GeneratedContent } from '@/types/api';
import { useContent } from '@/hooks/api';
import { useAuth } from '@/hooks/auth';
import {
  Search,
  Plus,
  Filter,
  MoreHorizontal,
  Edit,
  Trash2,
  Eye,
  FileText,
  Calendar,
  User,
  TrendingUp,
  Clock,
} from 'lucide-react';

interface ContentListProps {
  className?: string;
}

const ContentCard: React.FC<{ content: GeneratedContent }> = ({ content }) => {
  const [showActions, setShowActions] = useState(false);

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
    <Card className="group hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <FileText className="h-4 w-4 text-blue-500 flex-shrink-0" />
              <CardTitle className="text-lg truncate">{content.title}</CardTitle>
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
              {truncateText(content.brief, 120)}
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge variant={getStatusColor(content.status)}>
              {getStatusText(content.status)}
            </Badge>
            
            <div className="relative">
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setShowActions(!showActions)}
                className="h-8 w-8 opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <MoreHorizontal className="h-4 w-4" />
              </Button>
              
              {showActions && (
                <div className="absolute right-0 mt-2 w-48 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-10">
                  <div className="py-1">
                    <Link href={`/dashboard/content/${content.id}`}>
                      <button className="flex w-full items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                        <Eye className="h-4 w-4 mr-3" />
                        Просмотреть
                      </button>
                    </Link>
                    <Link href={`/dashboard/content/${content.id}`}>
                      <button className="flex w-full items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                        <Edit className="h-4 w-4 mr-3" />
                        Редактировать
                      </button>
                    </Link>
                    <button className="flex w-full items-center px-4 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20">
                      <Trash2 className="h-4 w-4 mr-3" />
                      Удалить
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="pt-0">
        <div className="space-y-3">
          {/* Style info */}
          {content.style_profile && (
            <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
              <div className="h-2 w-2 rounded-full bg-blue-500" />
              <span>Стиль: {content.style_profile.name}</span>
            </div>
          )}
          
          {/* Stats */}
          <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
            <div className="flex items-center space-x-1">
              <TrendingUp className="h-4 w-4" />
              <span>{content.token_count} токенов</span>
            </div>
            <div className="flex items-center space-x-1">
              <Clock className="h-4 w-4" />
              <span>{content.iterations?.length || 0} итераций</span>
            </div>
          </div>
          
          {/* Created info */}
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center space-x-1">
              <Calendar className="h-3 w-3" />
              <span>{formatDateTime(content.created_at)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <User className="h-3 w-3" />
              <span>Автор</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const ContentList: React.FC<ContentListProps> = ({ className }) => {
  const { organization } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  
  const { data: content, isLoading, error } = useContent(
    organization?.id || '',
    {
      query: searchQuery || undefined,
      status: statusFilter,
      per_page: 20,
      sort_by: 'created_at',
      sort_order: 'desc',
    }
  );

  if (isLoading) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Контент</h1>
          <SkeletonCard className="h-10 w-32" />
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="text-center py-12">
          <h3 className="text-lg font-medium text-gray-900 dark:text-white mb-2">
            Ошибка загрузки контента
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Не удалось загрузить список статей
          </p>
          <Button onClick={() => window.location.reload()}>
            Попробовать снова
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('space-y-6', className)}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-4 sm:space-y-0">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
            Контент
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Управляйте созданными статьями и материалами
          </p>
        </div>
        
        <Link href="/dashboard/content/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Создать статью
          </Button>
        </Link>
      </div>

      {/* Search and Filters */}
      <div className="flex flex-col sm:flex-row gap-4">
        <div className="flex-1">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="search"
              placeholder="Поиск статей..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant={statusFilter === undefined ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter(undefined)}
          >
            Все
          </Button>
          <Button
            variant={statusFilter === 'draft' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter('draft')}
          >
            Черновики
          </Button>
          <Button
            variant={statusFilter === 'generated' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter('generated')}
          >
            Сгенерированные
          </Button>
          <Button
            variant={statusFilter === 'published' ? 'default' : 'outline'}
            size="sm"
            onClick={() => setStatusFilter('published')}
          >
            Опубликованные
          </Button>
        </div>
      </div>

      {/* Content Grid */}
      {content && content.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {content.map((item) => (
            <ContentCard key={item.id} content={item} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <FileText className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">
            Пока нет статей
          </h3>
          <p className="mt-1 text-gray-600 dark:text-gray-400">
            Создайте свою первую статью с помощью ИИ
          </p>
          <div className="mt-6">
            <Link href="/dashboard/content/new">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Создать статью
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export { ContentList, ContentCard };
