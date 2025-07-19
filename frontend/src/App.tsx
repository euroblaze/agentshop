import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { StateManager } from '@/managers/StateManager'
import { RouteManager } from '@/managers/RouteManager'
import Header from '@components/Layout/Header'
import Footer from '@components/Layout/Footer'
import HomePage from '@pages/HomePage'
import ProductListPage from '@pages/ProductListPage'
import ProductDetailPage from '@pages/ProductDetailPage'
import SearchResultsPage from '@pages/SearchResultsPage'
import CheckoutPage from '@pages/CheckoutPage'
import OrderConfirmationPage from '@pages/OrderConfirmationPage'
import LoginPage from '@pages/CustomerAccount/LoginPage'
import RegisterPage from '@pages/CustomerAccount/RegisterPage'
import DashboardPage from '@pages/CustomerAccount/DashboardPage'
import OrderHistoryPage from '@pages/CustomerAccount/OrderHistoryPage'
import ProfilePage from '@pages/CustomerAccount/ProfilePage'
import SupportRequestPage from '@pages/CustomerAccount/SupportRequestPage'
import ProtectedRoute from '@/routes/ProtectedRoute'
import ErrorBoundary from '@components/UI/ErrorBoundary'

function App() {
  return (
    <ErrorBoundary>
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-grow">
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<HomePage />} />
            <Route path="/products" element={<ProductListPage />} />
            <Route path="/products/:id" element={<ProductDetailPage />} />
            <Route path="/search" element={<SearchResultsPage />} />
            <Route path="/checkout" element={<CheckoutPage />} />
            <Route path="/order-confirmation/:orderId" element={<OrderConfirmationPage />} />
            
            {/* Authentication Routes */}
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            
            {/* Protected Customer Routes */}
            <Route path="/account" element={<ProtectedRoute />}>
              <Route index element={<DashboardPage />} />
              <Route path="orders" element={<OrderHistoryPage />} />
              <Route path="profile" element={<ProfilePage />} />
              <Route path="support" element={<SupportRequestPage />} />
            </Route>
            
            {/* 404 Route */}
            <Route path="*" element={<div>Page Not Found</div>} />
          </Routes>
        </main>
        <Footer />
      </div>
    </ErrorBoundary>
  )
}

export default App