import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { ProductGallery } from '../components/ProductGallery';
import { LoadingSpinner } from '../components/ui/LoadingSpinner';
import { Button } from '../components/ui/Button';
import { Product } from '../models/Product';
import { productService, cartService } from '../services/ApiService';

export const ProductDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [quantity, setQuantity] = useState(1);
  const [addingToCart, setAddingToCart] = useState(false);
  const [addToCartMessage, setAddToCartMessage] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadProduct(parseInt(id));
    }
  }, [id]);

  const loadProduct = async (productId: number) => {
    try {
      setLoading(true);
      const productData = await productService.getById(productId);
      setProduct(productData);
    } catch (err) {
      setError('Failed to load product');
    } finally {
      setLoading(false);
    }
  };

  const handleAddToCart = async () => {
    if (!product) return;

    try {
      setAddingToCart(true);
      const result = await cartService.addToCart(product.id, quantity);
      
      if (result) {
        setAddToCartMessage('Product added to cart successfully!');
        setTimeout(() => setAddToCartMessage(null), 3000);
      } else {
        setAddToCartMessage('Failed to add product to cart');
        setTimeout(() => setAddToCartMessage(null), 3000);
      }
    } catch (err) {
      setAddToCartMessage('Error adding product to cart');
      setTimeout(() => setAddToCartMessage(null), 3000);
    } finally {
      setAddingToCart(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !product) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-red-600 mb-4">Product Not Found</h2>
          <p className="text-gray-600 mb-4">{error || 'The requested product could not be found.'}</p>
          <Link
            to="/products"
            className="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
          >
            Back to Products
          </Link>
        </div>
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
          <span className="text-gray-900">{product.name}</span>
        </div>
      </nav>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Product Images */}
        <div>
          <ProductGallery images={product.image_urls || []} productName={product.name} />
        </div>

        {/* Product Info */}
        <div className="space-y-6">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">{product.name}</h1>
            {product.category && (
              <p className="text-sm text-gray-600 mb-4">Category: {product.category}</p>
            )}
            <div className="flex items-center space-x-4 mb-4">
              <span className="text-3xl font-bold text-green-600">${product.price}</span>
              {product.stock_quantity !== undefined && (
                <span className={`text-sm px-2 py-1 rounded ${
                  product.stock_quantity > 0 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {product.stock_quantity > 0 ? `${product.stock_quantity} in stock` : 'Out of stock'}
                </span>
              )}
            </div>
          </div>

          {/* Description */}
          {product.description && (
            <div>
              <h3 className="text-lg font-semibold mb-2">Description</h3>
              <p className="text-gray-700 leading-relaxed">{product.description}</p>
            </div>
          )}

          {/* Add to Cart Section */}
          <div className="border-t pt-6">
            <div className="flex items-center space-x-4 mb-4">
              <label htmlFor="quantity" className="text-sm font-medium">Quantity:</label>
              <select
                id="quantity"
                value={quantity}
                onChange={(e) => setQuantity(parseInt(e.target.value))}
                className="border rounded px-3 py-2 w-20"
                disabled={!product.stock_quantity || product.stock_quantity === 0}
              >
                {Array.from({ length: Math.min(10, product.stock_quantity || 1) }, (_, i) => (
                  <option key={i + 1} value={i + 1}>{i + 1}</option>
                ))}
              </select>
            </div>

            <div className="space-y-3">
              <Button
                onClick={handleAddToCart}
                disabled={addingToCart || !product.stock_quantity || product.stock_quantity === 0}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400"
              >
                {addingToCart ? 'Adding...' : 'Add to Cart'}
              </Button>

              {addToCartMessage && (
                <div className={`text-sm p-3 rounded ${
                  addToCartMessage.includes('successfully') 
                    ? 'bg-green-100 text-green-800' 
                    : 'bg-red-100 text-red-800'
                }`}>
                  {addToCartMessage}
                </div>
              )}
            </div>
          </div>

          {/* Additional Info */}
          {(product.weight || product.dimensions) && (
            <div className="border-t pt-6">
              <h3 className="text-lg font-semibold mb-2">Product Details</h3>
              <div className="space-y-1 text-sm text-gray-600">
                {product.weight && <p>Weight: {product.weight}</p>}
                {product.dimensions && <p>Dimensions: {product.dimensions}</p>}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};