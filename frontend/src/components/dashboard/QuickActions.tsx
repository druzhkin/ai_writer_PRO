'use client';

// Quick actions component with buttons for creating new content and accessing features

import React from 'react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { cn } from '@/lib/utils';
import {
  Plus,
  FileText,
  Palette,
  Users,
  BarChart3,
  Settings,
  Upload,
  Zap,
} from 'lucide-react';

interface QuickActionProps {
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  href: string;
  variant?: 'default' | 'outline' | 'secondary';
  className?: string;
}

const QuickAction: React.FC<QuickActionProps> = ({
  title,
  description,
  icon: Icon,
  href,
  variant = 'outline',
  className,
}) => {
  return (
    <Link href={href} className={cn('block', className)}>
      <Card className="h-full transition-all duration-200 hover:shadow-md hover:scale-105 cursor-pointer">
        <CardContent className="p-6">
          <div className="flex items-center space-x-4">
            <div className="flex-shrink-0">
              <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10">
                <Icon className="h-6 w-6 text-primary" />
              </div>
            </div>
            <div className="flex-1 min-w-0">
              <h3 className="text-sm font-medium text-gray-900 dark:text-white">
                {title}
              </h3>
              <p className="text-sm text-gray-500 dark:text-gray-400">
                {description}
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
};

interface QuickActionsProps {
  className?: string;
}

const QuickActions: React.FC<QuickActionsProps> = ({ className }) => {
  const primaryActions = [
    {
      title: 'Создать контент',
      description: 'Сгенерировать новую статью с помощью ИИ',
      icon: FileText,
      href: '/dashboard/content/new',
      variant: 'default' as const,
    },
    {
      title: 'Добавить стиль',
      description: 'Создать новый стиль письма',
      icon: Palette,
      href: '/dashboard/styles/new',
      variant: 'outline' as const,
    },
  ];

  const secondaryActions = [
    {
      title: 'Загрузить файлы',
      description: 'Добавить референсные материалы',
      icon: Upload,
      href: '/dashboard/files',
      variant: 'outline' as const,
    },
    {
      title: 'Пригласить команду',
      description: 'Добавить новых участников',
      icon: Users,
      href: '/dashboard/team',
      variant: 'outline' as const,
    },
    {
      title: 'Аналитика',
      description: 'Посмотреть статистику использования',
      icon: BarChart3,
      href: '/dashboard/analytics',
      variant: 'outline' as const,
    },
    {
      title: 'Настройки',
      description: 'Управление организацией',
      icon: Settings,
      href: '/dashboard/settings',
      variant: 'outline' as const,
    },
  ];

  return (
    <div className={cn('space-y-6', className)}>
      {/* Primary Actions */}
      <div>
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
          Быстрые действия
        </h2>
        <div className="grid gap-4 md:grid-cols-2">
          {primaryActions.map((action, index) => (
            <QuickAction
              key={index}
              title={action.title}
              description={action.description}
              icon={action.icon}
              href={action.href}
              variant={action.variant}
            />
          ))}
        </div>
      </div>

      {/* Secondary Actions */}
      <div>
        <h3 className="text-md font-medium text-gray-700 dark:text-gray-300 mb-3">
          Другие действия
        </h3>
        <div className="grid gap-3 md:grid-cols-2 lg:grid-cols-4">
          {secondaryActions.map((action, index) => (
            <QuickAction
              key={index}
              title={action.title}
              description={action.description}
              icon={action.icon}
              href={action.href}
              variant={action.variant}
            />
          ))}
        </div>
      </div>

      {/* AI Assistant CTA */}
      <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-800">
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Zap className="h-5 w-5 text-blue-600 dark:text-blue-400" />
            <span className="text-blue-900 dark:text-blue-100">
              ИИ-помощник
            </span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-blue-800 dark:text-blue-200 mb-4">
            Получите персональные рекомендации по улучшению вашего контента и оптимизации стилей письма.
          </p>
          <Button className="bg-blue-600 hover:bg-blue-700 text-white">
            <Zap className="h-4 w-4 mr-2" />
            Запустить ИИ-помощника
          </Button>
        </CardContent>
      </Card>
    </div>
  );
};

export { QuickActions, QuickAction };
