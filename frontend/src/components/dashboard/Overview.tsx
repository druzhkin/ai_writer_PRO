'use client';

// Dashboard overview component with statistics, quick actions, and recent activity

import React from 'react';
import { StatsCards } from './StatsCards';
import { QuickActions } from './QuickActions';
import { RecentArticles } from './RecentArticles';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import { useAuth } from '@/hooks/auth';
import { useOrganizationUsage } from '@/store/organization';
import { useContent } from '@/hooks/api';
import { Loading, SkeletonCard } from '@/components/ui/Loading';
import {
  TrendingUp,
  Calendar,
  Target,
  Award,
} from 'lucide-react';

interface OverviewProps {
  className?: string;
}

const Overview: React.FC<OverviewProps> = ({ className }) => {
  const { user, organization } = useAuth();
  const { usageStats, loadUsageStats, isLoading: usageLoading } = useOrganizationUsage();
  const { data: content, isLoading: contentLoading } = useContent(
    organization?.id || '',
    { per_page: 5, sort_by: 'created_at', sort_order: 'desc' }
  );

  React.useEffect(() => {
    if (organization?.id) {
      loadUsageStats(organization.id);
    }
  }, [organization?.id, loadUsageStats]);

  const isLoading = usageLoading || contentLoading;

  if (isLoading) {
    return (
      <div className={cn('space-y-6', className)}>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {Array.from({ length: 6 }).map((_, i) => (
            <SkeletonCard key={i} />
          ))}
        </div>
        <div className="grid gap-6 lg:grid-cols-2">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      </div>
    );
  }

  const stats = {
    totalContent: content?.length || 0,
    totalStyles: 0, // TODO: Get from styles API
    totalTokens: usageStats?.total_tokens || 0,
    totalCost: usageStats?.total_cost || 0,
    teamMembers: 1, // TODO: Get from organization members
    avgGenerationTime: 45, // TODO: Calculate from actual data
  };

  return (
    <div className={cn('space-y-6', className)}>
      {/* Welcome Section */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 rounded-lg p-6 border border-blue-200 dark:border-blue-800">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
              Добро пожаловать, {user?.full_name}!
            </h1>
            <p className="mt-1 text-gray-600 dark:text-gray-400">
              Вот что происходит в вашей организации {organization?.name}
            </p>
          </div>
          <div className="hidden sm:block">
            <div className="flex items-center space-x-4 text-sm text-gray-600 dark:text-gray-400">
              <div className="flex items-center space-x-1">
                <Calendar className="h-4 w-4" />
                <span>{new Date().toLocaleDateString('ru-RU')}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Statistics Cards */}
      <StatsCards stats={stats} />

      {/* Main Content Grid */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Quick Actions */}
        <div className="lg:col-span-1">
          <QuickActions />
        </div>

        {/* Recent Articles */}
        <div className="lg:col-span-2">
          <RecentArticles articles={content} />
        </div>
      </div>

      {/* Additional Insights */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Usage Trend */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <TrendingUp className="h-5 w-5" />
              <span>Тренд использования</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Токены за неделю
                </span>
                <span className="text-sm font-medium">
                  {usageStats?.daily_usage?.slice(-7).reduce((sum, day) => sum + day.tokens, 0) || 0}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Стоимость за неделю
                </span>
                <span className="text-sm font-medium">
                  {new Intl.NumberFormat('ru-RU', {
                    style: 'currency',
                    currency: 'RUB',
                    minimumFractionDigits: 0,
                  }).format(usageStats?.daily_usage?.slice(-7).reduce((sum, day) => sum + day.cost, 0) || 0)}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-600 dark:text-gray-400">
                  Запросов за неделю
                </span>
                <span className="text-sm font-medium">
                  {usageStats?.daily_usage?.slice(-7).reduce((sum, day) => sum + day.requests, 0) || 0}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Goals */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Target className="h-5 w-5" />
              <span>Цели на месяц</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Статьи
                  </span>
                  <span className="text-sm font-medium">5 / 20</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div className="bg-blue-600 h-2 rounded-full" style={{ width: '25%' }} />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Стили
                  </span>
                  <span className="text-sm font-medium">2 / 10</span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div className="bg-green-600 h-2 rounded-full" style={{ width: '20%' }} />
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    Токены
                  </span>
                  <span className="text-sm font-medium">
                    {usageStats?.total_tokens || 0} / 100K
                  </span>
                </div>
                <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                  <div 
                    className="bg-purple-600 h-2 rounded-full" 
                    style={{ width: `${Math.min(((usageStats?.total_tokens || 0) / 100000) * 100, 100)}%` }} 
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Achievements */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Award className="h-5 w-5" />
              <span>Достижения</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              <div className="flex items-center space-x-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-yellow-100 dark:bg-yellow-900/20">
                  <Award className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Первая статья
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Создана {content?.[0] ? new Date(content[0].created_at).toLocaleDateString('ru-RU') : 'недавно'}
                  </p>
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/20">
                  <TrendingUp className="h-4 w-4 text-blue-600 dark:text-blue-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Активный пользователь
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    Использовано {usageStats?.total_tokens || 0} токенов
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export { Overview };
