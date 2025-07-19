import React from 'react';
import { Card, CardBody } from '../../ui/Card';

export interface MetricCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  change?: {
    value: string;
    trend: 'up' | 'down' | 'neutral';
  };
  icon?: React.ReactNode;
  color?: 'blue' | 'green' | 'yellow' | 'red' | 'purple';
}

export const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  subtitle,
  change,
  icon,
  color = 'blue'
}) => {
  const colorClasses = {
    blue: {
      bg: 'bg-blue-50',
      icon: 'text-blue-600',
      change: {
        up: 'text-green-600',
        down: 'text-red-600',
        neutral: 'text-gray-600'
      }
    },
    green: {
      bg: 'bg-green-50',
      icon: 'text-green-600',
      change: {
        up: 'text-green-600',
        down: 'text-red-600',
        neutral: 'text-gray-600'
      }
    },
    yellow: {
      bg: 'bg-yellow-50',
      icon: 'text-yellow-600',
      change: {
        up: 'text-green-600',
        down: 'text-red-600',
        neutral: 'text-gray-600'
      }
    },
    red: {
      bg: 'bg-red-50',
      icon: 'text-red-600',
      change: {
        up: 'text-green-600',
        down: 'text-red-600',
        neutral: 'text-gray-600'
      }
    },
    purple: {
      bg: 'bg-purple-50',
      icon: 'text-purple-600',
      change: {
        up: 'text-green-600',
        down: 'text-red-600',
        neutral: 'text-gray-600'
      }
    }
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'neutral') => {
    switch (trend) {
      case 'up':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 17l9.2-9.2M17 17V7m0 0H7" />
          </svg>
        );
      case 'down':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 7l-9.2 9.2M7 7v10m0 0h10" />
          </svg>
        );
      case 'neutral':
        return (
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14" />
          </svg>
        );
    }
  };

  return (
    <Card variant="elevated" className="hover:shadow-lg transition-shadow">
      <CardBody>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">{title}</h3>
              {icon && (
                <div className={`p-2 rounded-lg ${colorClasses[color].bg}`}>
                  <span className={`${colorClasses[color].icon}`}>
                    {icon}
                  </span>
                </div>
              )}
            </div>
            
            <div className="flex items-baseline">
              <p className="text-2xl font-bold text-gray-900">
                {typeof value === 'number' ? value.toLocaleString() : value}
              </p>
              {change && (
                <div className={`ml-2 flex items-center text-sm ${colorClasses[color].change[change.trend]}`}>
                  {getTrendIcon(change.trend)}
                  <span className="ml-1">{change.value}</span>
                </div>
              )}
            </div>
            
            {subtitle && (
              <p className="mt-1 text-sm text-gray-500">{subtitle}</p>
            )}
          </div>
        </div>
      </CardBody>
    </Card>
  );
};