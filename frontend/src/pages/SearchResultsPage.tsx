import React, { useState, useEffect } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import { ProductCard } from '../components/ProductCard';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Product } from '../models/Product';
import { productService } from '../services/ApiService';

export const SearchResultsPage: React.FC = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const query = searchParams.get('q') || '';
  const category = searchParams.get('category') || '';
  
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState('relevance');
  const [minPrice, setMinPrice] = useState('');
  const [maxPrice, setMaxPrice] = useState('');
  const [categories, setCategories] = useState<string[]>([]);

  useEffect(() => {
    if (query || category) {
      searchProducts();
    }
    loadCategories();
  }, [query, category, sortBy]);

  const searchProducts = async () => {
    try {
      setLoading(true);
      setError(null);

      const filters: Record<string, any> = {};
      
      if (category) {
        filters.category = category;
      }
      
      if (minPrice) {
        filters.min_price = parseFloat(minPrice);
      }
      
      if (maxPrice) {
        filters.max_price = parseFloat(maxPrice);
      }

      if (sortBy !== 'relevance') {
        filters.sort_by = sortBy;
      }

      let results: Product[] = [];
      
      if (query) {
        results = await productService.searchProducts(query, filters);
      } else if (category) {
        const productData = await productService.getProducts(1, 100, filters);
        results = productData.products;
      }

      // Apply client-side sorting if needed
      if (sortBy === 'price_low') {
        results.sort((a, b) => a.price - b.price);
      } else if (sortBy === 'price_high') {
        results.sort((a, b) => b.price - a.price);
      } else if (sortBy === 'name') {
        results.sort((a, b) => a.name.localeCompare(b.name));
      }

      setProducts(results);
    } catch (err) {
      setError('Failed to search products');
    } finally {
      setLoading(false);
    }
  };

  const loadCategories = async () => {
    try {
      const cats = await productService.getProductCategories();
      setCategories(cats);
    } catch (err) {
      console.error('Failed to load categories:', err);
    }
  };

  const handlePriceFilter = () => {
    searchProducts();
  };

  const handleCategoryFilter = (newCategory: string) => {
    const newSearchParams = new URLSearchParams(searchParams);
    if (newCategory) {
      newSearchParams.set('category', newCategory);
    } else {
      newSearchParams.delete('category');
    }
    setSearchParams(newSearchParams);
  };

  const clearFilters = () => {
    setMinPrice('');
    setMaxPrice('');
    setSortBy('relevance');
    const newSearchParams = new URLSearchParams();
    if (query) {
      newSearchParams.set('q', query);
    }
    setSearchParams(newSearchParams);
  };

  const getSearchTitle = () => {
    if (query && category) {
      return `Search results for "${query}" in ${category}`;
    } else if (query) {
      return `Search results for "${query}"`;
    } else if (category) {
      return `Products in ${category}`;
    }
    return 'Search Results';
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Breadcrumb */}
      <nav className="mb-6">
        <div className="flex items-center space-x-2 text-sm text-gray-600">
          <Link to="/" className="hover:text-blue-600">Home</Link>
          <span>/</span>
          <Link to="/products" className="hover:text-blue-600">Products</Link>
          <span>/</span>
          <span className="text-gray-900">Search Results</span>
        </div>
      </nav>

      <div className="flex flex-col lg:flex-row gap-8">
        {/* Sidebar - Filters */}
        <div className="w-full lg:w-1/4">
          <div className="bg-white rounded-lg shadow-md p-6 sticky top-4">
            <div className="flex justify-between items-center mb-4">
              <h3 className="text-lg font-semibold">Filters</h3>
              <button
                onClick={clearFilters}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Clear All
              </button>
            </div>

            {/* Categories */}
            <div className="mb-6">
              <h4 className="font-medium mb-3">Categories</h4>
              <div className="space-y-2">
                <button
                  onClick={() => handleCategoryFilter('')}
                  className={`block w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                    !category ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-100'
                  }`}
                >
                  All Categories
                </button>
                {categories.map((cat) => (
                  <button
                    key={cat}
                    onClick={() => handleCategoryFilter(cat)}
                    className={`block w-full text-left px-3 py-2 rounded text-sm transition-colors ${
                      category === cat ? 'bg-blue-100 text-blue-800' : 'hover:bg-gray-100'
                    }`}
                  >
                    {cat}
                  </button>
                ))}
              </div>
            </div>

            {/* Price Range */}
            <div className="mb-6">
              <h4 className="font-medium mb-3">Price Range</h4>
              <div className="space-y-3">
                <div className="flex items-center space-x-2">
                  <input
                    type="number"
                    placeholder="Min"
                    value={minPrice}
                    onChange={(e) => setMinPrice(e.target.value)}
                    className="w-full border rounded px-2 py-1 text-sm"
                  />
                  <span className="text-gray-500">-</span>
                  <input
                    type="number"
                    placeholder="Max"
                    value={maxPrice}
                    onChange={(e) => setMaxPrice(e.target.value)}
                    className="w-full border rounded px-2 py-1 text-sm"
                  />
                </div>
                <button
                  onClick={handlePriceFilter}
                  className="w-full bg-blue-600 text-white py-2 rounded text-sm hover:bg-blue-700"
                >
                  Apply
                </button>
              </div>
            </div>

            {/* Sort By */}
            <div>
              <h4 className="font-medium mb-3">Sort By</h4>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full border rounded px-3 py-2 text-sm"
              >
                <option value="relevance">Relevance</option>
                <option value="name">Name A-Z</option>
                <option value="price_low">Price: Low to High</option>
                <option value="price_high">Price: High to Low</option>
              </select>
            </div>
          </div>
        </div>

        {/* Main Content */}
        <div className="w-full lg:w-3/4">
          <div className="flex flex-col md:flex-row md:justify-between md:items-center mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">
                {getSearchTitle()}
              </h1>
              <p className="text-gray-600">
                {products.length} product{products.length !== 1 ? 's' : ''} found
              </p>
            </div>
          </div>

          {error && (
            <div className="bg-red-100 text-red-800 p-4 rounded-lg mb-6">
              {error}
            </div>
          )}

          {products.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-24 h-24 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-12 h-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-700 mb-2">No Products Found</h2>
              <p className="text-gray-600 mb-4">
                {query ? `No products found for "${query}"` : 'No products found with the current filters'}
              </p>
              <div className="space-x-4">
                <button
                  onClick={clearFilters}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                  Clear Filters
                </button>
                <Link
                  to="/products"
                  className="bg-gray-600 text-white px-4 py-2 rounded hover:bg-gray-700"
                >
                  Browse All Products
                </Link>
              </div>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {products.map((product) => (
                <ProductCard key={product.id} product={product} />
              ))}
            </div>
          )}

          {/* Search Tips */}
          {products.length === 0 && query && (
            <div className="mt-8 bg-blue-50 rounded-lg p-6">
              <h3 className="font-semibold text-blue-900 mb-2">Search Tips</h3>
              <ul className="text-blue-800 text-sm space-y-1">
                <li>• Check your spelling</li>
                <li>• Try more general keywords</li>
                <li>• Use fewer keywords</li>
                <li>• Browse our categories to discover products</li>
              </ul>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};