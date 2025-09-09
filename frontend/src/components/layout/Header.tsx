'use client';

// Header component with user menu, organization switcher, notifications, and search functionality

import React, { useState } from 'react';
import { useAuth } from '@/hooks/auth';
import { useCurrentOrganization } from '@/store/organization';
import { Button } from '@/components/ui/Button';
import { Input } from '@/components/ui/Input';
import { Modal } from '@/components/ui/Modal';
import {
  Search,
  Bell,
  Plus,
  User,
  Settings,
  LogOut,
  Building2,
  ChevronDown,
  Menu,
} from 'lucide-react';
import { cn } from '@/lib/utils';

interface HeaderProps {
  onMenuClick?: () => void;
  showMenuButton?: boolean;
}

const Header: React.FC<HeaderProps> = ({ onMenuClick, showMenuButton = false }) => {
  const { user, logout } = useAuth();
  const { organization, setCurrentOrganization } = useCurrentOrganization();
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [showOrgMenu, setShowOrgMenu] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  const handleLogout = async () => {
    await logout();
    setShowUserMenu(false);
  };

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // Implement search functionality
    console.log('Search query:', searchQuery);
  };

  return (
    <header className="h-16 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between px-4 lg:px-6">
      {/* Left side */}
      <div className="flex items-center space-x-4">
        {showMenuButton && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onMenuClick}
            className="lg:hidden"
          >
            <Menu className="h-5 w-5" />
          </Button>
        )}
        
        {/* Search */}
        <form onSubmit={handleSearch} className="hidden md:block">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
            <Input
              type="search"
              placeholder="Поиск контента, стилей..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 w-64"
            />
          </div>
        </form>
      </div>

      {/* Right side */}
      <div className="flex items-center space-x-4">
        {/* Quick Actions */}
        <div className="hidden sm:flex items-center space-x-2">
          <Button size="sm" variant="outline">
            <Plus className="h-4 w-4 mr-2" />
            Новый контент
          </Button>
        </div>

        {/* Notifications */}
        <Button variant="ghost" size="icon" className="relative">
          <Bell className="h-5 w-5" />
          <span className="absolute -top-1 -right-1 h-3 w-3 rounded-full bg-red-500 text-xs text-white flex items-center justify-center">
            3
          </span>
        </Button>

        {/* Organization Switcher */}
        {organization && (
          <div className="relative">
            <Button
              variant="ghost"
              onClick={() => setShowOrgMenu(!showOrgMenu)}
              className="flex items-center space-x-2"
            >
              <Building2 className="h-4 w-4" />
              <span className="hidden sm:block truncate max-w-32">
                {organization.name}
              </span>
              <ChevronDown className="h-4 w-4" />
            </Button>

            {showOrgMenu && (
              <div className="absolute right-0 mt-2 w-64 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-50">
                <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                  <p className="text-sm font-medium text-gray-900 dark:text-white">
                    Организации
                  </p>
                </div>
                <div className="p-2">
                  <div className="p-2 rounded-md bg-blue-50 dark:bg-blue-900/20">
                    <p className="text-sm font-medium text-blue-900 dark:text-blue-200">
                      {organization.name}
                    </p>
                    <p className="text-xs text-blue-600 dark:text-blue-400">
                      Текущая организация
                    </p>
                  </div>
                </div>
                <div className="p-2 border-t border-gray-200 dark:border-gray-700">
                  <Button variant="ghost" size="sm" className="w-full justify-start">
                    <Plus className="h-4 w-4 mr-2" />
                    Создать организацию
                  </Button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* User Menu */}
        <div className="relative">
          <Button
            variant="ghost"
            onClick={() => setShowUserMenu(!showUserMenu)}
            className="flex items-center space-x-2"
          >
            <div className="h-8 w-8 rounded-full bg-gray-300 dark:bg-gray-600 flex items-center justify-center">
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                {user?.full_name?.charAt(0).toUpperCase()}
              </span>
            </div>
            <span className="hidden sm:block text-sm font-medium">
              {user?.full_name}
            </span>
            <ChevronDown className="h-4 w-4" />
          </Button>

          {showUserMenu && (
            <div className="absolute right-0 mt-2 w-56 bg-white dark:bg-gray-800 rounded-md shadow-lg border border-gray-200 dark:border-gray-700 z-50">
              <div className="p-3 border-b border-gray-200 dark:border-gray-700">
                <p className="text-sm font-medium text-gray-900 dark:text-white">
                  {user?.full_name}
                </p>
                <p className="text-xs text-gray-500 dark:text-gray-400">
                  {user?.email}
                </p>
              </div>
              
              <div className="p-1">
                <button className="flex w-full items-center px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md">
                  <User className="h-4 w-4 mr-3" />
                  Профиль
                </button>
                <button className="flex w-full items-center px-3 py-2 text-sm text-gray-700 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md">
                  <Settings className="h-4 w-4 mr-3" />
                  Настройки
                </button>
              </div>
              
              <div className="p-1 border-t border-gray-200 dark:border-gray-700">
                <button
                  onClick={handleLogout}
                  className="flex w-full items-center px-3 py-2 text-sm text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-md"
                >
                  <LogOut className="h-4 w-4 mr-3" />
                  Выйти
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Click outside handlers */}
      {(showUserMenu || showOrgMenu) && (
        <div
          className="fixed inset-0 z-40"
          onClick={() => {
            setShowUserMenu(false);
            setShowOrgMenu(false);
          }}
        />
      )}
    </header>
  );
};

export { Header };
