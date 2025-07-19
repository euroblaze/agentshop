import React from 'react';
import { NavLink } from 'react-router-dom';
import { Button } from '../../ui/Button';

export const CustomerHeader: React.FC = () => {
  // TODO: Get customer data from context/state
  const customer = {
    name: 'John Doe',
    tier: 'gold', // bronze, silver, gold, platinum
    avatar: null
  };

  const handleLogout = () => {
    // TODO: Implement logout logic
    console.log('Logout clicked');
  };

  const getTierDisplay = (tier: string) => {
    const tiers = {
      bronze: { name: 'Bronze', class: 'tier-bronze' },
      silver: { name: 'Silver', class: 'tier-silver' },
      gold: { name: 'Gold', class: 'tier-gold' },
      platinum: { name: 'Platinum', class: 'tier-platinum' }
    };
    return tiers[tier as keyof typeof tiers] || tiers.bronze;
  };

  const tierInfo = getTierDisplay(customer.tier);

  return (
    <header className="bg-white border-b border-purple-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* Logo and nav */}
          <div className="flex items-center">
            <NavLink to="/" className="flex items-center">
              <h1 className="text-xl font-bold text-purple-600">AgentShop</h1>
            </NavLink>
            <nav className="hidden md:flex ml-8 space-x-4">
              <NavLink 
                to="/shop" 
                className="text-gray-600 hover:text-purple-600 px-3 py-2 rounded-md text-sm font-medium"
              >
                Shop
              </NavLink>
              <NavLink 
                to="/account" 
                className="text-purple-600 bg-purple-50 px-3 py-2 rounded-md text-sm font-medium"
              >
                My Account
              </NavLink>
            </nav>
          </div>

          {/* User info and actions */}
          <div className="flex items-center space-x-4">
            {/* Customer tier badge */}
            <span className={`tier-badge theme-customer ${tierInfo.class}`}>
              {tierInfo.name} Member
            </span>

            {/* Customer greeting */}
            <div className="hidden sm:flex items-center">
              <span className="text-sm text-gray-600">Welcome back,</span>
              <span className="ml-1 text-sm font-medium text-gray-900">{customer.name}</span>
            </div>

            {/* Avatar */}
            <div className="flex items-center">
              {customer.avatar ? (
                <img className="h-8 w-8 rounded-full" src={customer.avatar} alt={customer.name} />
              ) : (
                <div className="h-8 w-8 rounded-full bg-purple-100 flex items-center justify-center">
                  <span className="text-sm font-medium text-purple-600">
                    {customer.name.split(' ').map(n => n[0]).join('')}
                  </span>
                </div>
              )}
            </div>

            {/* Logout button */}
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={handleLogout}
              className="text-gray-600 hover:text-gray-900"
            >
              Logout
            </Button>
          </div>
        </div>
      </div>
    </header>
  );
};