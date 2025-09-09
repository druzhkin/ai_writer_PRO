'use client';

// Dashboard layout component with sidebar navigation and main content area

import React, { useState } from 'react';
import { useProtectedRoute } from '@/hooks/auth';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { Loading } from '@/components/ui/Loading';
import { cn } from '@/lib/utils';

interface DashboardLayoutProps {
  children: React.ReactNode;
  className?: string;
}

const DashboardLayout: React.FC<DashboardLayoutProps> = ({ children, className }) => {
  const { isLoading } = useProtectedRoute();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed(!sidebarCollapsed);
  };

  const toggleMobileMenu = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Loading text="Загрузка..." />
      </div>
    );
  }

  return (
    <div className="h-screen flex overflow-hidden bg-gray-50 dark:bg-gray-900">
      {/* Sidebar */}
      <div className={cn(
        'hidden lg:flex lg:flex-shrink-0 transition-all duration-300',
        sidebarCollapsed ? 'lg:w-16' : 'lg:w-64'
      )}>
        <Sidebar isCollapsed={sidebarCollapsed} onToggle={toggleSidebar} />
      </div>

      {/* Mobile sidebar overlay */}
      {mobileMenuOpen && (
        <div className="fixed inset-0 z-40 lg:hidden">
          <div className="fixed inset-0 bg-gray-600 bg-opacity-75" onClick={toggleMobileMenu} />
          <div className="relative flex w-64 flex-1 flex-col">
            <Sidebar isCollapsed={false} onToggle={toggleMobileMenu} />
          </div>
        </div>
      )}

      {/* Main content */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Header */}
        <Header 
          onMenuClick={toggleMobileMenu} 
          showMenuButton={true}
        />

        {/* Page content */}
        <main className="flex-1 overflow-y-auto">
          <div className={cn('p-4 lg:p-6', className)}>
            {children}
          </div>
        </main>
      </div>
    </div>
  );
};

export { DashboardLayout };
