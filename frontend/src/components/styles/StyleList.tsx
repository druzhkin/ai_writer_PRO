'use client';

// Style list component for displaying style profiles with search, filtering, and pagination

import React, { useState } from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Badge } from '@/components/ui/Badge';
import { Loading, SkeletonCard } from '@/components/ui/Loading';
import { cn, formatDateTime, truncateText } from '@/lib/utils';
import { StyleProfile } from '@/types/api';
import { useStyles } from '@/hooks/api';
import { useAuth } from '@/hooks/auth';
import {
  Search,
  Plus,
  Filter,
  MoreHorizontal,
  Edit,
  Trash2,
  Eye,
  Palette,
  FileText,
  Calendar,
  User,
} from 'lucide-react';

interface StyleListProps {
  className?: string;
}

const StyleCard: React.FC<{ style: StyleProfile }> = ({ style }) => {
  const [showActions, setShowActions] = useState(false);

  return (
    <Card className="group hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex-1 min-w-0">
            <div className="flex items-center space-x-2 mb-2">
              <Palette className="h-4 w-4 text-blue-500 flex-shrink-0" />
              <CardTitle className="text-lg truncate">{style.name}</CardTitle>
            </div>
            {style.description && (
              <p className="text-sm text-gray-600 dark:text-gray-400 line-clamp-2">
                {style.description}
              </p>
            )}
          </div>
          
          <div className="flex items-center space-x-2">
            <Badge variant={style.is_active ? 'success' : 'secondary'}>
              {style.is_active ? 'Активен' : 'Неактивен'}
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
                    <Link href={`/dashboard/styles/${style.id}`}>
                      <button className="flex w-full items-center px-4 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700">
                        <Eye className="h-4 w-4 mr-3" />
                        Просмотреть
                      </button>
                    </Link>
                    <Link href={`/dashboard/styles/${style.id}/edit`}>
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
          {/* Reference articles count */}
          <div className="flex items-center space-x-2 text-sm text-gray-600 dark:text-gray-400">
            <FileText className="h-4 w-4" />
            <span>{style.reference_articles?.length || 0} референсных статей</span>
          </div>
          
          {/* Analysis status */}
          {style.analysis_result ? (
            <div className="flex items-center space-x-2 text-sm text-green-600 dark:text-green-400">
              <div className="h-2 w-2 rounded-full bg-green-500" />
              <span>Анализ завершен</span>
            </div>
          ) : (
            <div className="flex items-center space-x-2 text-sm text-yellow-600 dark:text-yellow-400">
              <div className="h-2 w-2 rounded-full bg-yellow-500" />
              <span>Анализ в процессе</span>
            </div>
          )}
          
          {/* Created info */}
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center space-x-1">
              <Calendar className="h-3 w-3" />
              <span>{formatDateTime(style.created_at)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <User className="h-3 w-3" />
              <span>Создатель</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

const StyleList: React.FC<StyleListProps> = ({ className }) => {
  const { organization } = useAuth();
  const [searchQuery, setSearchQuery] = useState('');
  const [filterActive, setFilterActive] = useState<boolean | undefined>(undefined);
  
  const { data: styles, isLoading, error } = useStyles(
    organization?.id || '',
    {
      query: searchQuery || undefined,
      is_active: filterActive,
      per_page: 20,
    }
  );

  if (isLoading) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="flex items-center justify-between">
          <h1 className="text-2xl font-bold">Стили</h1>
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
            Ошибка загрузки стилей
          </h3>
          <p className="text-gray-600 dark:text-gray-400 mb-4">
            Не удалось загрузить список стилей
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
            Стили
          </h1>
          <p className="text-gray-600 dark:text-gray-400">
            Управляйте стилями письма для генерации контента
          </p>
        </div>
        
        <Link href="/dashboard/styles/new">
          <Button>
            <Plus className="h-4 w-4 mr-2" />
            Создать стиль
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
              placeholder="Поиск стилей..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10"
            />
          </div>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button
            variant={filterActive === undefined ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterActive(undefined)}
          >
            Все
          </Button>
          <Button
            variant={filterActive === true ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterActive(true)}
          >
            Активные
          </Button>
          <Button
            variant={filterActive === false ? 'default' : 'outline'}
            size="sm"
            onClick={() => setFilterActive(false)}
          >
            Неактивные
          </Button>
        </div>
      </div>

      {/* Styles Grid */}
      {styles && styles.length > 0 ? (
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {styles.map((style) => (
            <StyleCard key={style.id} style={style} />
          ))}
        </div>
      ) : (
        <div className="text-center py-12">
          <Palette className="mx-auto h-12 w-12 text-gray-400" />
          <h3 className="mt-2 text-lg font-medium text-gray-900 dark:text-white">
            Пока нет стилей
          </h3>
          <p className="mt-1 text-gray-600 dark:text-gray-400">
            Создайте свой первый стиль письма
          </p>
          <div className="mt-6">
            <Link href="/dashboard/styles/new">
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Создать стиль
              </Button>
            </Link>
          </div>
        </div>
      )}
    </div>
  );
};

export { StyleList, StyleCard };
