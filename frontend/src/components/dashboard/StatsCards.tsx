'use client';

// Statistics cards component for displaying key metrics

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import {
  FileText,
  Palette,
  TrendingUp,
  DollarSign,
  Users,
  Clock,
} from 'lucide-react';

interface StatCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: 'increase' | 'decrease' | 'neutral';
  };
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  className?: string;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  change,
  icon: Icon,
  description,
  className,
}) => {
  const getChangeColor = (type: string) => {
    switch (type) {
      case 'increase':
        return 'text-green-600 dark:text-green-400';
      case 'decrease':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  const getChangeIcon = (type: string) => {
    switch (type) {
      case 'increase':
        return '↗';
      case 'decrease':
        return '↘';
      default:
        return '→';
    }
  };

  return (
    <Card className={cn('', className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {title}
        </CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {change && (
          <div className="flex items-center space-x-1 text-xs">
            <span className={getChangeColor(change.type)}>
              {getChangeIcon(change.type)} {Math.abs(change.value)}%
            </span>
            <span className="text-muted-foreground">за последний месяц</span>
          </div>
        )}
        {description && (
          <p className="text-xs text-muted-foreground mt-1">{description}</p>
        )}
      </CardContent>
    </Card>
  );
};

interface StatsCardsProps {
  stats?: {
    totalContent: number;
    totalStyles: number;
    totalTokens: number;
    totalCost: number;
    teamMembers: number;
    avgGenerationTime: number;
  };
  className?: string;
}

const StatsCards: React.FC<StatsCardsProps> = ({ stats, className }) => {
  const defaultStats = {
    totalContent: 0,
    totalStyles: 0,
    totalTokens: 0,
    totalCost: 0,
    teamMembers: 0,
    avgGenerationTime: 0,
  };

  const currentStats = stats || defaultStats;

  const formatNumber = (num: number) => {
    if (num >= 1000000) {
      return (num / 1000000).toFixed(1) + 'M';
    }
    if (num >= 1000) {
      return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
  };

  const formatCost = (cost: number) => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 2,
    }).format(cost);
  };

  const formatTime = (seconds: number) => {
    if (seconds < 60) {
      return `${seconds}с`;
    }
    return `${Math.floor(seconds / 60)}м ${seconds % 60}с`;
  };

  return (
    <div className={cn('grid gap-4 md:grid-cols-2 lg:grid-cols-3', className)}>
      <StatCard
        title="Всего контента"
        value={formatNumber(currentStats.totalContent)}
        change={{ value: 12, type: 'increase' }}
        icon={FileText}
        description="Созданных статей и материалов"
      />
      
      <StatCard
        title="Стилей"
        value={currentStats.totalStyles}
        change={{ value: 3, type: 'increase' }}
        icon={Palette}
        description="Настроенных стилей письма"
      />
      
      <StatCard
        title="Использовано токенов"
        value={formatNumber(currentStats.totalTokens)}
        change={{ value: 8, type: 'increase' }}
        icon={TrendingUp}
        description="За текущий месяц"
      />
      
      <StatCard
        title="Потрачено"
        value={formatCost(currentStats.totalCost)}
        change={{ value: 5, type: 'increase' }}
        icon={DollarSign}
        description="На генерацию контента"
      />
      
      <StatCard
        title="Участников команды"
        value={currentStats.teamMembers}
        change={{ value: 0, type: 'neutral' }}
        icon={Users}
        description="Активных пользователей"
      />
      
      <StatCard
        title="Среднее время генерации"
        value={formatTime(currentStats.avgGenerationTime)}
        change={{ value: 15, type: 'decrease' }}
        icon={Clock}
        description="Время создания статьи"
      />
    </div>
  );
};

export { StatsCards, StatCard };
