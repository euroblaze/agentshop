import React, { forwardRef } from 'react';

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  help?: string;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  variant?: 'default' | 'filled' | 'outlined';
  inputSize?: 'sm' | 'md' | 'lg';
}

export const Input = forwardRef<HTMLInputElement, InputProps>(({
  label,
  error,
  help,
  icon,
  iconPosition = 'left',
  variant = 'default',
  inputSize = 'md',
  className = '',
  id,
  ...props
}, ref) => {
  const inputId = id || `input-${Math.random().toString(36).substr(2, 9)}`;

  const baseInputClasses = [
    'block',
    'w-full',
    'border',
    'rounded-md',
    'transition-colors',
    'focus:outline-none',
    'focus:ring-2',
    'focus:ring-offset-2',
    'disabled:opacity-50',
    'disabled:cursor-not-allowed'
  ];

  const variantClasses = {
    default: [
      'bg-white',
      'border-gray-300',
      'text-gray-900',
      'placeholder-gray-400',
      'focus:border-blue-500',
      'focus:ring-blue-500'
    ],
    filled: [
      'bg-gray-50',
      'border-gray-200',
      'text-gray-900',
      'placeholder-gray-500',
      'focus:bg-white',
      'focus:border-blue-500',
      'focus:ring-blue-500'
    ],
    outlined: [
      'bg-transparent',
      'border-2',
      'border-gray-300',
      'text-gray-900',
      'placeholder-gray-400',
      'focus:border-blue-500',
      'focus:ring-blue-500'
    ]
  };

  const sizeClasses = {
    sm: ['px-3', 'py-1.5', 'text-sm'],
    md: ['px-3', 'py-2', 'text-sm'],
    lg: ['px-4', 'py-3', 'text-base']
  };

  const errorClasses = error ? [
    'border-red-300',
    'text-red-900',
    'placeholder-red-300',
    'focus:border-red-500',
    'focus:ring-red-500'
  ] : [];

  const iconClasses = icon ? (iconPosition === 'left' ? ['pl-10'] : ['pr-10']) : [];

  const inputClasses = [
    ...baseInputClasses,
    ...variantClasses[variant],
    ...sizeClasses[inputSize],
    ...(error ? errorClasses : []),
    ...iconClasses,
    className
  ].join(' ');

  const renderIcon = () => {
    if (!icon) return null;
    
    const positionClasses = iconPosition === 'left' 
      ? ['left-3']
      : ['right-3'];
      
    const iconSizeClasses = inputSize === 'lg' ? ['h-5', 'w-5'] : ['h-4', 'w-4'];
    const iconColorClasses = error ? ['text-red-400'] : ['text-gray-400'];
    
    return (
      <div className={[
        'absolute',
        'inset-y-0',
        'flex',
        'items-center',
        'pointer-events-none',
        ...positionClasses
      ].join(' ')}>
        <span className={[...iconSizeClasses, ...iconColorClasses].join(' ')}>
          {icon}
        </span>
      </div>
    );
  };

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-sm font-medium text-gray-700 mb-1">
          {label}
        </label>
      )}
      <div className="relative">
        <input
          ref={ref}
          id={inputId}
          className={inputClasses}
          {...props}
        />
        {renderIcon()}
      </div>
      {error && (
        <p className="mt-1 text-sm text-red-600">
          {error}
        </p>
      )}
      {help && !error && (
        <p className="mt-1 text-sm text-gray-500">
          {help}
        </p>
      )}
    </div>
  );
});

Input.displayName = 'Input';