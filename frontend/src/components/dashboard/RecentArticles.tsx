'use client';

// Recent articles component showing the latest generated content

import React from 'react';
import Link from 'next/link';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { cn, formatDateTime, truncateText } from '@/lib/utils';
import { GeneratedContent } from '@/types/api';
import {
  FileText,
  Clock,
  Eye,
  Edit,
  MoreHorizontal,
  TrendingUp,
} from 'lucide-react';

interface RecentArticlesProps {
  articles?: GeneratedContent[];
  maxItems?: number;
  className?: string;
}

const ArticleCard: React.FC<{ article: GeneratedContent }> = ({ article }) => {
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'published':
        return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
      case 'edited':
        return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
      case 'generated':
        return 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/20 dark:text-yellow-400';
      default:
        return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
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
    <div className="group relative">
      <Card className="h-full transition-all duration-200 hover:shadow-md">
        <CardContent className="p-4">
          <div className="flex items-start justify-between">
            <div className="flex-1 min-w-0">
              <div className="flex items-center space-x-2 mb-2">
                <FileText className="h-4 w-4 text-gray-400 flex-shrink-0" />
                <h3 className="text-sm font-medium text-gray-900 dark:text-white truncate">
                  {article.title}
                </h3>
              </div>
              
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-3 line-clamp-2">
                {truncateText(article.brief, 100)}
              </p>
              
              <div className="flex items-center space-x-4 text-xs text-gray-500 dark:text-gray-400">
                <div className="flex items-center space-x-1">
                  <Clock className="h-3 w-3" />
                  <span>{formatDateTime(article.created_at)}</span>
                </div>
                <div className="flex items-center space-x-1">
                  <TrendingUp className="h-3 w-3" />
                  <span>{article.token_count} токенов</span>
                </div>
              </div>
            </div>
            
            <div className="flex flex-col items-end space-y-2">
              <Badge className={getStatusColor(article.status)}>
                {getStatusText(article.status)}
              </Badge>
              
              <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <Link href={`/dashboard/content/${article.id}`}>
                  <Button variant="ghost" size="sm">
                    <Eye className="h-3 w-3" />
                  </Button>
                </Link>
                <Link href={`/dashboard/content/${article.id}`}>
                  <Button variant="ghost" size="sm">
                    <Edit className="h-3 w-3" />
                  </Button>
                </Link>
                <Button variant="ghost" size="sm">
                  <MoreHorizontal className="h-3 w-3" />
                </Button>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

const RecentArticles: React.FC<RecentArticlesProps> = ({ 
  articles = [], 
  maxItems = 5,
  className 
}) => {
  const recentArticles = articles.slice(0, maxItems);

  if (recentArticles.length === 0) {
    return (
      <Card className={className}>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Последние статьи</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8">
            <FileText className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900 dark:text-white">
              Пока нет статей
            </h3>
            <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
              Создайте свою первую статью с помощью ИИ
            </p>
            <div className="mt-6">
              <Link href="/dashboard/content/new">
                <Button>
                  <FileText className="h-4 w-4 mr-2" />
                  Создать статью
                </Button>
              </Link>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <span>Последние статьи</span>
          </CardTitle>
          <Link href="/dashboard/content">
            <Button variant="ghost" size="sm">
              Показать все
            </Button>
          </Link>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {recentArticles.map((article) => (
            <ArticleCard key={article.id} article={article} />
          ))}
        </div>
        
        {articles.length > maxItems && (
          <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
            <Link href="/dashboard/content">
              <Button variant="outline" className="w-full">
                Показать все статьи ({articles.length})
              </Button>
            </Link>
          </div>
        )}
      </CardContent>
    </Card>
  );
};

export { RecentArticles, ArticleCard };
