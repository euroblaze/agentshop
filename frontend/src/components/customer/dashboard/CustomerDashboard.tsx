import React from 'react';
import { Card, CardHeader, CardBody } from '../../ui/Card';
import { Button } from '../../ui/Button';

export const CustomerDashboard: React.FC = () => {
  // TODO: Replace with real data from API
  const customer = {
    name: 'John Doe',
    email: 'john@example.com',
    tier: 'gold',
    loyaltyPoints: 2456,
    totalOrders: 12,
    totalSpent: 1234.56
  };

  const recentOrders = [
    { id: 'ORD-001', date: '2024-01-15', total: 299.99, status: 'completed' },
    { id: 'ORD-002', date: '2024-01-10', total: 149.99, status: 'processing' },
    { id: 'ORD-003', date: '2024-01-05', total: 89.99, status: 'completed' }
  ];

  const getStatusBadge = (status: string) => {
    const statusClasses = {
      completed: 'order-status completed',
      processing: 'order-status processing',
      pending: 'order-status pending',
      cancelled: 'order-status cancelled'
    };

    return (
      <span className={statusClasses[status as keyof typeof statusClasses] || statusClasses.pending}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    );
  };

  return (
    <div className="space-y-6">
      {/* Welcome section */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">
          Welcome back, {customer.name}!
        </h1>
        <p className="mt-1 text-sm text-gray-600">
          Here's an overview of your account activity.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card variant="elevated">
          <CardBody>
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Total Orders</p>
                <p className="text-2xl font-bold text-gray-900">{customer.totalOrders}</p>
              </div>
              <div className="p-3 bg-blue-50 rounded-lg">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l-1 7a2 2 0 01-2 2H8a2 2 0 01-2-2L5 9z" />
                </svg>
              </div>
            </div>
          </CardBody>
        </Card>

        <Card variant="elevated">
          <CardBody>
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Total Spent</p>
                <p className="text-2xl font-bold text-gray-900">${customer.totalSpent.toLocaleString()}</p>
              </div>
              <div className="p-3 bg-green-50 rounded-lg">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
                </svg>
              </div>
            </div>
          </CardBody>
        </Card>

        <Card variant="elevated">
          <CardBody>
            <div className="flex items-center">
              <div className="flex-1">
                <p className="text-sm font-medium text-gray-600">Loyalty Points</p>
                <p className="text-2xl font-bold text-purple-600">{customer.loyaltyPoints.toLocaleString()}</p>
              </div>
              <div className="p-3 bg-purple-50 rounded-lg">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.196-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
                </svg>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>

      {/* Recent orders */}
      <Card variant="elevated">
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900">Recent Orders</h2>
            <Button variant="outline" size="sm">
              View All Orders
            </Button>
          </div>
        </CardHeader>
        <CardBody>
          {recentOrders.length > 0 ? (
            <div className="space-y-4">
              {recentOrders.map((order) => (
                <div key={order.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                  <div className="flex-1">
                    <div className="flex items-center space-x-4">
                      <div>
                        <p className="text-sm font-medium text-gray-900">{order.id}</p>
                        <p className="text-sm text-gray-500">{order.date}</p>
                      </div>
                      <div className="text-sm font-medium text-gray-900">
                        ${order.total.toFixed(2)}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-4">
                    {getStatusBadge(order.status)}
                    <Button variant="outline" size="sm">
                      View Details
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l-1 7a2 2 0 01-2 2H8a2 2 0 01-2-2L5 9z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No orders yet</h3>
              <p className="mt-1 text-sm text-gray-500">Get started by placing your first order.</p>
              <div className="mt-6">
                <Button>
                  Browse Products
                </Button>
              </div>
            </div>
          )}
        </CardBody>
      </Card>

      {/* Quick actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card variant="outlined">
          <CardBody>
            <div className="text-center">
              <div className="mx-auto w-12 h-12 bg-purple-50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">Update Profile</h3>
              <p className="mt-2 text-sm text-gray-500">
                Keep your personal information up to date.
              </p>
              <div className="mt-4">
                <Button variant="outline" fullWidth>
                  Edit Profile
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>

        <Card variant="outlined">
          <CardBody>
            <div className="text-center">
              <div className="mx-auto w-12 h-12 bg-green-50 rounded-lg flex items-center justify-center">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="mt-4 text-lg font-medium text-gray-900">Need Help?</h3>
              <p className="mt-2 text-sm text-gray-500">
                Get support from our customer service team.
              </p>
              <div className="mt-4">
                <Button variant="outline" fullWidth>
                  Contact Support
                </Button>
              </div>
            </div>
          </CardBody>
        </Card>
      </div>
    </div>
  );
};