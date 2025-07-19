import React from 'react';
import { Card } from '../../ui/Card';
import { Button } from '../../ui/Button';

export interface ProductCardProps {
  id: string;
  name: string;
  description: string;
  price: number;
  originalPrice?: number;
  imageUrl?: string;
  category: string;
  rating?: number;
  reviewCount?: number;
  inStock: boolean;
  onAddToCart?: (productId: string) => void;
  onQuickView?: (productId: string) => void;
}

export const ProductCard: React.FC<ProductCardProps> = ({
  id,
  name,
  description,
  price,
  originalPrice,
  imageUrl,
  category,
  rating = 0,
  reviewCount = 0,
  inStock,
  onAddToCart,
  onQuickView
}) => {
  const isOnSale = originalPrice && originalPrice > price;
  const discount = isOnSale ? Math.round(((originalPrice - price) / originalPrice) * 100) : 0;

  const renderStars = (rating: number) => {
    const stars = [];
    const fullStars = Math.floor(rating);
    const hasHalfStar = rating % 1 !== 0;

    for (let i = 0; i < 5; i++) {
      if (i < fullStars) {
        stars.push(
          <svg key={i} className="w-4 h-4 text-yellow-400 fill-current" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        );
      } else if (i === fullStars && hasHalfStar) {
        stars.push(
          <svg key={i} className="w-4 h-4 text-yellow-400 fill-current" viewBox="0 0 24 24">
            <defs>
              <linearGradient id="half-star" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="50%" stopColor="currentColor" />
                <stop offset="50%" stopColor="#e5e7eb" />
              </linearGradient>
            </defs>
            <path fill="url(#half-star)" d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        );
      } else {
        stars.push(
          <svg key={i} className="w-4 h-4 text-gray-300 fill-current" viewBox="0 0 24 24">
            <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z" />
          </svg>
        );
      }
    }

    return stars;
  };

  const handleAddToCart = () => {
    if (onAddToCart && inStock) {
      onAddToCart(id);
    }
  };

  const handleQuickView = () => {
    if (onQuickView) {
      onQuickView(id);
    }
  };

  return (
    <Card className="product-card group cursor-pointer transition-all duration-300 hover:shadow-lg relative overflow-hidden">
      {/* Sale badge */}
      {isOnSale && (
        <div className="absolute top-2 left-2 z-10 bg-red-500 text-white px-2 py-1 rounded-md text-xs font-bold">
          -{discount}%
        </div>
      )}

      {/* Stock status */}
      {!inStock && (
        <div className="absolute top-2 right-2 z-10 bg-gray-500 text-white px-2 py-1 rounded-md text-xs font-bold">
          Out of Stock
        </div>
      )}

      {/* Product image */}
      <div className="product-image relative overflow-hidden aspect-square bg-gray-100">
        {imageUrl ? (
          <img
            src={imageUrl}
            alt={name}
            className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
            onError={(e) => {
              (e.target as HTMLImageElement).src = '/api/placeholder/300/300';
            }}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center bg-gray-200">
            <svg className="w-16 h-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
          </div>
        )}

        {/* Overlay actions */}
        <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all duration-300 flex items-center justify-center">
          <div className="opacity-0 group-hover:opacity-100 transition-opacity duration-300 space-x-2">
            <Button variant="outline" size="sm" onClick={handleQuickView}>
              Quick View
            </Button>
          </div>
        </div>
      </div>

      {/* Product info */}
      <div className="p-4">
        {/* Category */}
        <div className="text-xs text-gray-500 uppercase tracking-wide mb-2">
          {category}
        </div>

        {/* Product name */}
        <h3 className="font-semibold text-gray-900 text-sm mb-2 line-clamp-2">
          {name}
        </h3>

        {/* Description */}
        <p className="text-gray-600 text-xs mb-3 line-clamp-2">
          {description}
        </p>

        {/* Rating */}
        {rating > 0 && (
          <div className="flex items-center space-x-2 mb-3">
            <div className="flex items-center">
              {renderStars(rating)}
            </div>
            <span className="text-xs text-gray-500">
              {rating.toFixed(1)} ({reviewCount})
            </span>
          </div>
        )}

        {/* Price */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <span className="price-tag text-lg font-bold">
              ${price.toFixed(2)}
            </span>
            {isOnSale && (
              <span className="text-sm text-gray-500 line-through">
                ${originalPrice?.toFixed(2)}
              </span>
            )}
          </div>
        </div>

        {/* Add to cart button */}
        <Button
          variant="primary"
          size="sm"
          fullWidth
          disabled={!inStock}
          onClick={handleAddToCart}
          className={inStock ? '' : 'opacity-50 cursor-not-allowed'}
        >
          {inStock ? 'Add to Cart' : 'Out of Stock'}
        </Button>
      </div>
    </Card>
  );
};