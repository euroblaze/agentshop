import React from 'react';
import { AdminLayout } from '../../components/admin/layout/AdminLayout';
import { MetricCard } from '../../components/admin/dashboard/MetricCard';
import { DashboardGrid } from '../../components/admin/dashboard/DashboardGrid';
import { Card, CardHeader, CardBody } from '../../components/ui/Card';

export const AdminDashboard: React.FC = () => {
  // TODO: Replace with real data from API
  const metrics = {
    totalCustomers: 1234,
    totalOrders: 567,
    totalProducts: 89,
    totalRevenue: '$12,345'
  };

  return (
    <AdminLayout>
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
          <p className="mt-1 text-sm text-gray-600">
            Welcome back! Here's what's happening with your store today.
          </p>
        </div>

        {/* Metrics Grid */}
        <DashboardGrid columns={4}>
          <MetricCard
            title="Total Customers"
            value={metrics.totalCustomers}
            change={{ value: '+12%', trend: 'up' }}
            color="blue"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
              </svg>
            }
          />
          
          <MetricCard
            title="Total Orders"
            value={metrics.totalOrders}
            change={{ value: '+8%', trend: 'up' }}
            color="green"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l-1 7a2 2 0 01-2 2H8a2 2 0 01-2-2L5 9z" />
              </svg>
            }
          />
          
          <MetricCard
            title="Total Products"
            value={metrics.totalProducts}
            change={{ value: '+3%', trend: 'up' }}
            color="purple"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
              </svg>
            }
          />
          
          <MetricCard
            title="Total Revenue"
            value={metrics.totalRevenue}
            change={{ value: '+23%', trend: 'up' }}
            color="green"
            icon={
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1" />
              </svg>
            }
          />
        </DashboardGrid>

        {/* Charts and Tables */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card variant="elevated">
            <CardHeader>
              <h2 className="text-lg font-semibold text-gray-900">Recent Orders</h2>
            </CardHeader>
            <CardBody>
              <div className="text-sm text-gray-500">
                Order tracking and management dashboard will be implemented here.
              </div>
            </CardBody>
          </Card>

          <Card variant="elevated">
            <CardHeader>
              <h2 className="text-lg font-semibold text-gray-900">Revenue Chart</h2>
            </CardHeader>
            <CardBody>
              <div className="text-sm text-gray-500">
                Revenue analytics and charts will be implemented here.
              </div>
            </CardBody>
          </Card>
        </div>

        {/* Recent Activity */}
        <Card variant="elevated">
          <CardHeader>
            <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
          </CardHeader>
          <CardBody>
            <div className="text-sm text-gray-500">
              Recent system activity and user actions will be displayed here.
            </div>
          </CardBody>
        </Card>
      </div>
    </AdminLayout>
  );
};