import React, { forwardRef } from 'react';
import { BaseComponent } from '../BaseComponent';

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost' | 'danger' | 'success';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  fullWidth?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(({
  variant = 'primary',
  size = 'md',
  loading = false,
  icon,
  iconPosition = 'left',
  fullWidth = false,
  disabled,
  children,
  className = '',
  ...props
}, ref) => {
  const baseClasses = [
    'inline-flex',
    'items-center',
    'justify-center',
    'font-medium',
    'border',
    'transition-all',
    'duration-200',
    'focus:outline-none',
    'focus:ring-2',
    'focus:ring-offset-2',
    'disabled:opacity-50',
    'disabled:cursor-not-allowed'
  ];

  const variantClasses = {
    primary: [
      'bg-blue-600',
      'text-white',
      'border-blue-600',
      'hover:bg-blue-700',
      'hover:border-blue-700',
      'focus:ring-blue-500',
      'active:bg-blue-800'
    ],
    secondary: [
      'bg-gray-600',
      'text-white', 
      'border-gray-600',
      'hover:bg-gray-700',
      'hover:border-gray-700',
      'focus:ring-gray-500',
      'active:bg-gray-800'
    ],
    outline: [
      'bg-white',
      'text-gray-700',
      'border-gray-300',
      'hover:bg-gray-50',
      'hover:border-gray-400',
      'focus:ring-blue-500',
      'active:bg-gray-100'
    ],
    ghost: [
      'bg-transparent',
      'text-gray-600',
      'border-transparent',
      'hover:bg-gray-100',
      'hover:text-gray-900',
      'focus:ring-gray-500',
      'active:bg-gray-200'
    ],
    danger: [
      'bg-red-600',
      'text-white',
      'border-red-600', 
      'hover:bg-red-700',
      'hover:border-red-700',
      'focus:ring-red-500',
      'active:bg-red-800'
    ],
    success: [
      'bg-green-600',
      'text-white',
      'border-green-600',
      'hover:bg-green-700', 
      'hover:border-green-700',
      'focus:ring-green-500',
      'active:bg-green-800'
    ]
  };

  const sizeClasses = {
    sm: ['px-3', 'py-1.5', 'text-sm', 'rounded-md'],
    md: ['px-4', 'py-2', 'text-sm', 'rounded-md'],
    lg: ['px-6', 'py-3', 'text-base', 'rounded-lg']
  };

  const widthClasses = fullWidth ? ['w-full'] : [];

  const allClasses = [
    ...baseClasses,
    ...variantClasses[variant],
    ...sizeClasses[size],
    ...widthClasses,
    className
  ].join(' ');

  const LoadingSpinner = () => (
    <svg className="animate-spin -ml-1 mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24">
      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
    </svg>
  );

  const renderIcon = () => {
    if (loading) return <LoadingSpinner />;
    if (!icon) return null;
    
    const iconClasses = children 
      ? (iconPosition === 'right' ? 'ml-2' : 'mr-2')
      : '';
      
    return <span className={iconClasses}>{icon}</span>;
  };

  return (
    <button
      ref={ref}
      className={allClasses}
      disabled={disabled || loading}
      {...props}
    >
      {iconPosition === 'left' && renderIcon()}
      {children}
      {iconPosition === 'right' && renderIcon()}
    </button>
  );
});

Button.displayName = 'Button';