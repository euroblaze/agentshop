import React from 'react';
import { ShopHeader } from './ShopHeader';
import { ShopFooter } from './ShopFooter';

export interface ShopLayoutProps {
  children: React.ReactNode;
}

export const ShopLayout: React.FC<ShopLayoutProps> = ({ children }) => {
  return (
    <div className="theme-shop min-h-screen bg-gray-50">
      <ShopHeader />
      
      <main className="min-h-screen">
        {children}
      </main>
      
      <ShopFooter />
    </div>
  );
};