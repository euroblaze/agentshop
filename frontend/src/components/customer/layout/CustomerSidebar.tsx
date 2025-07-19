import React from 'react';
import { NavLink } from 'react-router-dom';

interface NavItem {
  name: string;
  href: string;
  icon: React.ReactNode;
}

const navigation: NavItem[] = [
  {
    name: 'Dashboard',
    href: '/account',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2-2z" />
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5a2 2 0 012-2h4a2 2 0 012 2v6H8V5z" />
      </svg>
    ),
  },
  {
    name: 'Order History',
    href: '/account/orders',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l-1 7a2 2 0 01-2 2H8a2 2 0 01-2-2L5 9z" />
      </svg>
    ),
  },
  {
    name: 'Downloads',
    href: '/account/downloads',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M9 19l3 3m0 0l3-3m-3 3V10" />
      </svg>
    ),
  },
  {
    name: 'Profile',
    href: '/account/profile',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
      </svg>
    ),
  },
  {
    name: 'Support',
    href: '/account/support',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
];

export const CustomerSidebar: React.FC = () => {
  return (
    <nav className="space-y-1">
      <div className="bg-white rounded-lg shadow-sm border border-purple-100 p-4 mb-6">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Account Navigation</h3>
        <ul className="space-y-1">
          {navigation.map((item) => (
            <li key={item.name}>
              <NavLink
                to={item.href}
                end={item.href === '/account'}
                className={({ isActive }) =>
                  `account-nav-item group flex items-center px-3 py-2 text-sm font-medium rounded-md transition-colors ${
                    isActive
                      ? 'active bg-purple-50 text-purple-700'
                      : 'text-gray-600 hover:bg-purple-25 hover:text-purple-600'
                  }`
                }
              >
                <span className="mr-3 flex-shrink-0">
                  {item.icon}
                </span>
                {item.name}
              </NavLink>
            </li>
          ))}
        </ul>
      </div>

      {/* Quick stats */}
      <div className="bg-white rounded-lg shadow-sm border border-purple-100 p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Quick Stats</h3>
        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Total Orders:</span>
            <span className="font-medium text-gray-900">12</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Total Spent:</span>
            <span className="font-medium text-gray-900">$1,234</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Loyalty Points:</span>
            <span className="font-medium text-purple-600">2,456</span>
          </div>
        </div>
      </div>
    </nav>
  );
};