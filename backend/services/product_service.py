#!/usr/bin/env python3
"""
Product Service - Business logic for product management
"""

from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from ..models.product_models import Product, ProductCategory, ProductVariant
from ..core.orm.base_model import db_manager


class ProductService:
    """Service for product management operations"""
    
    def __init__(self, session: Optional[Session] = None):
        self.session = session or db_manager.get_session()
    
    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Get product by ID"""
        return self.session.query(Product).filter(
            and_(Product.id == product_id, Product.is_active == True)
        ).first()
    
    def get_all(self, page: int = 1, per_page: int = 20, filters: Optional[Dict] = None) -> Tuple[List[Product], int]:
        """Get all products with pagination"""
        query = self.session.query(Product).filter(Product.is_active == True)
        
        # Apply filters
        if filters:
            if 'category' in filters:
                query = query.filter(Product.category == filters['category'])
            if 'min_price' in filters:
                query = query.filter(Product.price >= filters['min_price'])
            if 'max_price' in filters:
                query = query.filter(Product.price <= filters['max_price'])
        
        total = query.count()
        products = query.offset((page - 1) * per_page).limit(per_page).all()
        
        return products, total
    
    def search_products(self, query: str, filters: Optional[Dict] = None) -> List[Product]:
        """Search products by name or description"""
        search_query = self.session.query(Product).filter(
            and_(
                Product.is_active == True,
                or_(
                    Product.name.ilike(f'%{query}%'),
                    Product.description.ilike(f'%{query}%')
                )
            )
        )
        
        # Apply additional filters
        if filters:
            if 'category' in filters:
                search_query = search_query.filter(Product.category == filters['category'])
        
        return search_query.all()
    
    def get_categories(self) -> List[str]:
        """Get all product categories"""
        categories = self.session.query(Product.category).filter(
            and_(Product.category.isnot(None), Product.is_active == True)
        ).distinct().all()
        
        return [cat[0] for cat in categories if cat[0]]
    
    def create_product(self, product_data: Dict[str, Any]) -> Product:
        """Create a new product"""
        product = Product(**product_data)
        self.session.add(product)
        self.session.commit()
        return product
    
    def update_product(self, product_id: int, update_data: Dict[str, Any]) -> Optional[Product]:
        """Update product information"""
        product = self.get_by_id(product_id)
        if product:
            for key, value in update_data.items():
                if hasattr(product, key):
                    setattr(product, key, value)
            self.session.commit()
        return product
    
    def delete_product(self, product_id: int) -> bool:
        """Soft delete a product"""
        product = self.get_by_id(product_id)
        if product:
            product.soft_delete()
            self.session.commit()
            return True
        return False