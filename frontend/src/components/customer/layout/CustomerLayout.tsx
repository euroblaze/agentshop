import React from 'react';
import { CustomerSidebar } from './CustomerSidebar';
import { CustomerHeader } from './CustomerHeader';

export interface CustomerLayoutProps {
  children: React.ReactNode;
}

export const CustomerLayout: React.FC<CustomerLayoutProps> = ({ children }) => {
  return (
    <div className="theme-customer min-h-screen bg-purple-50">
      <CustomerHeader />
      
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="lg:grid lg:grid-cols-12 lg:gap-x-8">
          {/* Sidebar */}
          <aside className="lg:col-span-3">
            <CustomerSidebar />
          </aside>

          {/* Main content */}
          <main className="mt-8 lg:mt-0 lg:col-span-9">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
};