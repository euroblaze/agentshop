import React, { useState } from 'react';
import { NavLink } from 'react-router-dom';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';

export const ShopHeader: React.FC = () => {
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  
  // TODO: Get cart count from state/context
  const cartCount = 3;

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    // TODO: Implement search functionality
    console.log('Search:', searchQuery);
  };

  const navigation = [
    { name: 'Home', href: '/' },
    { name: 'Products', href: '/products' },
    { name: 'Categories', href: '/categories' },
    { name: 'About', href: '/about' },
    { name: 'Contact', href: '/contact' }
  ];

  return (
    <header className="bg-white shadow-sm border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Top bar */}
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <NavLink to="/" className="flex items-center">
              <h1 className="text-2xl font-bold text-emerald-600">AgentShop</h1>
            </NavLink>
          </div>

          {/* Desktop navigation */}
          <nav className="hidden lg:flex items-center space-x-8">
            {navigation.map((item) => (
              <NavLink
                key={item.name}
                to={item.href}
                className={({ isActive }) =>
                  `text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-emerald-600'
                      : 'text-gray-600 hover:text-emerald-600'
                  }`
                }
              >
                {item.name}
              </NavLink>
            ))}
          </nav>

          {/* Search, Cart, and Account */}
          <div className="flex items-center space-x-4">
            {/* Search - Desktop */}
            <form onSubmit={handleSearch} className="hidden md:flex">
              <div className="relative">
                <Input
                  type="search"
                  placeholder="Search products..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-64"
                  icon={
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                  }
                />
              </div>
            </form>

            {/* Cart */}
            <NavLink to="/cart" className="relative p-2 text-gray-600 hover:text-emerald-600 transition-colors">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4m1.6 8L6 11H5m2 2l1 9h10l1-9M9 19v1a2 2 0 11-4 0v-1m14 0v1a2 2 0 11-4 0v-1" />
              </svg>
              {cartCount > 0 && (
                <span className="cart-badge absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center text-xs font-bold">
                  {cartCount > 99 ? '99+' : cartCount}
                </span>
              )}
            </NavLink>

            {/* Account */}
            <div className="flex items-center space-x-2">
              <NavLink to="/login">
                <Button variant="ghost" size="sm">
                  Sign In
                </Button>
              </NavLink>
              <NavLink to="/register">
                <Button variant="primary" size="sm">
                  Sign Up
                </Button>
              </NavLink>
            </div>

            {/* Mobile menu button */}
            <button
              type="button"
              className="lg:hidden p-2 text-gray-600 hover:text-emerald-600"
              onClick={() => setIsMenuOpen(!isMenuOpen)}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                {isMenuOpen ? (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                ) : (
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                )}
              </svg>
            </button>
          </div>
        </div>

        {/* Mobile menu */}
        {isMenuOpen && (
          <div className="lg:hidden border-t border-gray-200 py-4 space-y-4">
            {/* Mobile search */}
            <form onSubmit={handleSearch} className="px-4">
              <Input
                type="search"
                placeholder="Search products..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                icon={
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                  </svg>
                }
              />
            </form>

            {/* Mobile navigation */}
            <nav className="px-4 space-y-2">
              {navigation.map((item) => (
                <NavLink
                  key={item.name}
                  to={item.href}
                  className={({ isActive }) =>
                    `block py-2 text-base font-medium transition-colors ${
                      isActive
                        ? 'text-emerald-600'
                        : 'text-gray-600 hover:text-emerald-600'
                    }`
                  }
                  onClick={() => setIsMenuOpen(false)}
                >
                  {item.name}
                </NavLink>
              ))}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
};