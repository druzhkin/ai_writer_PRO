// Dashboard layout for protected routes with sidebar navigation and organization context

import React from 'react';
import { DashboardLayout } from '@/components/layout/DashboardLayout';

interface DashboardLayoutProps {
  children: React.ReactNode;
}

const DashboardLayoutWrapper: React.FC<DashboardLayoutProps> = ({ children }) => {
  return <DashboardLayout>{children}</DashboardLayout>;
};

export default DashboardLayoutWrapper;
