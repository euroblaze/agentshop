import React from 'react';

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: 'default' | 'outlined' | 'elevated' | 'filled';
  padding?: 'none' | 'sm' | 'md' | 'lg';
}

export interface CardHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  border?: boolean;
}

export interface CardBodyProps extends React.HTMLAttributes<HTMLDivElement> {}

export interface CardFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  border?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(({
  variant = 'default',
  padding = 'none',
  className = '',
  children,
  ...props
}, ref) => {
  const baseClasses = ['rounded-lg', 'overflow-hidden'];
  
  const variantClasses = {
    default: ['bg-white', 'border', 'border-gray-200'],
    outlined: ['bg-white', 'border-2', 'border-gray-300'],
    elevated: ['bg-white', 'shadow-md', 'border', 'border-gray-100'],
    filled: ['bg-gray-50', 'border', 'border-gray-200']
  };

  const paddingClasses = {
    none: [],
    sm: ['p-4'],
    md: ['p-6'], 
    lg: ['p-8']
  };

  const allClasses = [
    ...baseClasses,
    ...variantClasses[variant],
    ...paddingClasses[padding],
    className
  ].join(' ');

  return (
    <div ref={ref} className={allClasses} {...props}>
      {children}
    </div>
  );
});

Card.displayName = 'Card';

export const CardHeader = React.forwardRef<HTMLDivElement, CardHeaderProps>(({
  border = true,
  className = '',
  children,
  ...props
}, ref) => {
  const baseClasses = ['px-6', 'py-4'];
  const borderClasses = border ? ['border-b', 'border-gray-200', 'bg-gray-50'] : [];
  
  const allClasses = [...baseClasses, ...borderClasses, className].join(' ');

  return (
    <div ref={ref} className={allClasses} {...props}>
      {children}
    </div>
  );
});

CardHeader.displayName = 'CardHeader';

export const CardBody = React.forwardRef<HTMLDivElement, CardBodyProps>(({
  className = '',
  children,
  ...props
}, ref) => {
  const allClasses = ['px-6', 'py-4', className].join(' ');

  return (
    <div ref={ref} className={allClasses} {...props}>
      {children}
    </div>
  );
});

CardBody.displayName = 'CardBody';

export const CardFooter = React.forwardRef<HTMLDivElement, CardFooterProps>(({
  border = true,
  className = '',
  children,
  ...props
}, ref) => {
  const baseClasses = ['px-6', 'py-4'];
  const borderClasses = border ? ['border-t', 'border-gray-200', 'bg-gray-50'] : [];
  
  const allClasses = [...baseClasses, ...borderClasses, className].join(' ');

  return (
    <div ref={ref} className={allClasses} {...props}>
      {children}
    </div>
  );
});

CardFooter.displayName = 'CardFooter';