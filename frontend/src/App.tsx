import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { StateManager } from '@/managers/StateManager'
import { RouteManager } from '@/managers/RouteManager'

// Import new components
import { HomePage } from '@pages/HomePage'
import { AdminDashboard } from '@pages/admin/AdminDashboard'
import { CustomerLayout } from '@components/customer/layout/CustomerLayout'
import { CustomerDashboard } from '@components/customer/dashboard/CustomerDashboard'

// Legacy imports that need to be created
import ProductListPage from '@pages/ProductListPage'
import ProductDetailPage from '@pages/ProductDetailPage'
import SearchResultsPage from '@pages/SearchResultsPage'
import CheckoutPage from '@pages/CheckoutPage'
import OrderConfirmationPage from '@pages/OrderConfirmationPage'
import LoginPage from '@pages/CustomerAccount/LoginPage'
import RegisterPage from '@pages/CustomerAccount/RegisterPage'
import OrderHistoryPage from '@pages/CustomerAccount/OrderHistoryPage'
import ProfilePage from '@pages/CustomerAccount/ProfilePage'
import SupportRequestPage from '@pages/CustomerAccount/SupportRequestPage'
import ProtectedRoute from '@/routes/ProtectedRoute'
import ErrorBoundary from '@components/UI/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen">
        <Routes>
          {/* Public Shop Routes */}
          <Route path="/" element={<HomePage />} />
          <Route path="/products" element={<ProductListPage />} />
          <Route path="/products/:id" element={<ProductDetailPage />} />
          <Route path="/search" element={<SearchResultsPage />} />
          <Route path="/checkout" element={<CheckoutPage />} />
          <Route path="/order-confirmation/:orderId" element={<OrderConfirmationPage />} />
          
          {/* Authentication Routes */}
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          
          {/* Admin Routes */}
          <Route path="/admin" element={<AdminDashboard />} />
          <Route path="/admin/*" element={<AdminDashboard />} />
          
          {/* Protected Customer Routes */}
          <Route path="/account" element={<ProtectedRoute />}>
            <Route index element={
              <CustomerLayout>
                <CustomerDashboard />
              </CustomerLayout>
            } />
            <Route path="orders" element={
              <CustomerLayout>
                <OrderHistoryPage />
              </CustomerLayout>
            } />
            <Route path="profile" element={
              <CustomerLayout>
                <ProfilePage />
              </CustomerLayout>
            } />
            <Route path="support" element={
              <CustomerLayout>
                <SupportRequestPage />
              </CustomerLayout>
            } />
          </Route>
          
          {/* 404 Route */}
          <Route path="*" element={<div className="min-h-screen flex items-center justify-center">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-gray-900 mb-4">404</h1>
              <p className="text-gray-600">Page Not Found</p>
            </div>
          </div>} />
        </Routes>
      </div>
    </ErrorBoundary>
  )
}

export default App