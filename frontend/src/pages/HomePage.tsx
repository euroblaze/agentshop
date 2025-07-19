import React from 'react';
import { ShopLayout } from '../components/shop/layout/ShopLayout';
import { ProductCard } from '../components/shop/product/ProductCard';
import { Button } from '../components/ui/Button';
import { Card, CardBody } from '../components/ui/Card';

export const HomePage: React.FC = () => {
  // TODO: Replace with real data from API
  const featuredProducts = [
    {
      id: '1',
      name: 'Odoo Enterprise Suite',
      description: 'Complete business management solution with CRM, inventory, accounting and more.',
      price: 299.99,
      originalPrice: 399.99,
      category: 'Business Software',
      rating: 4.8,
      reviewCount: 124,
      inStock: true,
      imageUrl: '/api/placeholder/300/300'
    },
    {
      id: '2', 
      name: 'AI Agent Development Kit',
      description: 'Professional toolkit for building and deploying intelligent agents.',
      price: 199.99,
      category: 'Development Tools',
      rating: 4.6,
      reviewCount: 89,
      inStock: true,
      imageUrl: '/api/placeholder/300/300'
    },
    {
      id: '3',
      name: 'Custom Implementation Service',
      description: 'Professional consultation and implementation services for your business needs.',
      price: 1299.99,
      category: 'Services',
      rating: 4.9,
      reviewCount: 45,
      inStock: true,
      imageUrl: '/api/placeholder/300/300'
    },
    {
      id: '4',
      name: 'Premium Support Package',
      description: '24/7 dedicated support with priority response and custom solutions.',
      price: 99.99,
      category: 'Support',
      rating: 4.7,
      reviewCount: 67,
      inStock: false,
      imageUrl: '/api/placeholder/300/300'
    }
  ];

  const handleAddToCart = (productId: string) => {
    console.log('Add to cart:', productId);
    // TODO: Implement add to cart functionality
  };

  const handleQuickView = (productId: string) => {
    console.log('Quick view:', productId);
    // TODO: Implement quick view functionality
  };

  return (
    <ShopLayout>
      {/* Hero section */}
      <section className="bg-gradient-to-br from-emerald-50 to-teal-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
              Premium Digital
              <span className="text-emerald-600 block">Solutions</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
              Discover cutting-edge software, AI agents, and professional services 
              designed to transform your business operations.
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="px-8 py-3">
                Browse Products
              </Button>
              <Button variant="outline" size="lg" className="px-8 py-3">
                Learn More
              </Button>
            </div>
          </div>
        </div>
      </section>

      {/* Features section */}
      <section className="py-16 bg-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Why Choose AgentShop?
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              We provide enterprise-grade solutions with professional support and seamless integration.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <Card className="text-center p-6 border-gray-200 hover:border-emerald-200 transition-colors">
              <CardBody>
                <div className="w-12 h-12 bg-emerald-50 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Quality Assured</h3>
                <p className="text-gray-600">
                  Every product is thoroughly tested and comes with comprehensive documentation.
                </p>
              </CardBody>
            </Card>

            <Card className="text-center p-6 border-gray-200 hover:border-emerald-200 transition-colors">
              <CardBody>
                <div className="w-12 h-12 bg-emerald-50 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192L5.636 18.364M12 2.25a9.75 9.75 0 010 19.5" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">24/7 Support</h3>
                <p className="text-gray-600">
                  Round-the-clock support from our expert team to help you succeed.
                </p>
              </CardBody>
            </Card>

            <Card className="text-center p-6 border-gray-200 hover:border-emerald-200 transition-colors">
              <CardBody>
                <div className="w-12 h-12 bg-emerald-50 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">Fast Delivery</h3>
                <p className="text-gray-600">
                  Instant downloads and quick implementation to get you started immediately.
                </p>
              </CardBody>
            </Card>
          </div>
        </div>
      </section>

      {/* Featured products */}
      <section className="py-16 bg-gray-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 mb-4">
              Featured Products
            </h2>
            <p className="text-lg text-gray-600 max-w-2xl mx-auto">
              Explore our most popular and highly-rated digital solutions.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
            {featuredProducts.map((product) => (
              <ProductCard
                key={product.id}
                {...product}
                onAddToCart={handleAddToCart}
                onQuickView={handleQuickView}
              />
            ))}
          </div>

          <div className="text-center">
            <Button variant="outline" size="lg">
              View All Products
            </Button>
          </div>
        </div>
      </section>

      {/* CTA section */}
      <section className="py-16 bg-emerald-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to Transform Your Business?
          </h2>
          <p className="text-xl text-emerald-100 mb-8 max-w-2xl mx-auto">
            Join thousands of satisfied customers who trust AgentShop for their digital transformation needs.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Button variant="secondary" size="lg" className="px-8 py-3 bg-white text-emerald-600 hover:bg-gray-50">
              Get Started Today
            </Button>
            <Button variant="outline" size="lg" className="px-8 py-3 border-white text-white hover:bg-white hover:text-emerald-600">
              Contact Sales
            </Button>
          </div>
        </div>
      </section>
    </ShopLayout>
  );
};