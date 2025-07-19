#!/usr/bin/env python3
"""
Product Repository - Data access layer for product-related operations
Provides specialized queries and operations for products, categories, reviews, and inquiries
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc

from .base_repository import BaseRepository
from ..models.product_models import Product, ProductCategory, ProductReview, ProductInquiry, ProductStatus, PriceType


class ProductRepository(BaseRepository[Product]):
    """Repository for Product entities with specialized product operations"""
    
    def __init__(self, session: Session = None):
        super().__init__(Product, session)
    
    def get_active_products(self, 
                           limit: int = None, 
                           offset: int = None,
                           category_id: int = None) -> List[Product]:
        """
        Get all active (published) products
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            category_id: Optional category filter
            
        Returns:
            List of active products
        """
        query = self.session.query(Product).filter(
            and_(
                Product.status == ProductStatus.ACTIVE.value,
                Product.is_deleted != 'Y'
            )
        )
        
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        query = query.order_by(desc(Product.created_at))
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_featured_products(self, limit: int = 6) -> List[Product]:
        """
        Get featured products for homepage display
        
        Args:
            limit: Maximum number of featured products
            
        Returns:
            List of featured products
        """
        return self.session.query(Product).filter(
            and_(
                Product.status == ProductStatus.ACTIVE.value,
                Product.is_deleted != 'Y',
                Product.featured_image.isnot(None)
            )
        ).order_by(
            desc(Product.thumbs_up_count),
            desc(Product.view_count)
        ).limit(limit).all()
    
    def get_by_slug(self, slug: str) -> Optional[Product]:
        """
        Get product by URL slug
        
        Args:
            slug: URL-friendly product identifier
            
        Returns:
            Product instance or None
        """
        return self.session.query(Product).filter(
            Product.slug == slug
        ).first()
    
    def search_products(self, 
                       search_term: str,
                       category_id: int = None,
                       price_type: str = None,
                       min_price: float = None,
                       max_price: float = None,
                       limit: int = 50,
                       offset: int = None) -> List[Product]:
        """
        Search products with multiple filters
        
        Args:
            search_term: Text to search in name, title, description
            category_id: Filter by category
            price_type: Filter by price type (fixed, inquiry, free)
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching products
        """
        query = self.session.query(Product).filter(
            and_(
                Product.status == ProductStatus.ACTIVE.value,
                Product.is_deleted != 'Y'
            )
        )
        
        # Text search across multiple fields
        if search_term:
            search_conditions = or_(
                Product.name.ilike(f"%{search_term}%"),
                Product.title.ilike(f"%{search_term}%"),
                Product.short_description.ilike(f"%{search_term}%"),
                Product.keywords.ilike(f"%{search_term}%")
            )
            query = query.filter(search_conditions)
        
        # Category filter
        if category_id:
            query = query.filter(Product.category_id == category_id)
        
        # Price type filter
        if price_type:
            query = query.filter(Product.price_type == price_type)
        
        # Price range filters
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        # Order by relevance (could be enhanced with full-text search)
        query = query.order_by(
            desc(Product.thumbs_up_count),
            desc(Product.view_count),
            Product.name
        )
        
        if offset:
            query = query.offset(offset)
        
        return query.limit(limit).all()
    
    def get_products_by_category(self, category_id: int, 
                                limit: int = None, 
                                offset: int = None) -> List[Product]:
        """
        Get products in a specific category
        
        Args:
            category_id: Category ID
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of products in category
        """
        query = self.session.query(Product).filter(
            and_(
                Product.category_id == category_id,
                Product.status == ProductStatus.ACTIVE.value,
                Product.is_deleted != 'Y'
            )
        ).order_by(Product.name)
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_related_products(self, product: Product, limit: int = 4) -> List[Product]:
        """
        Get products related to the given product
        
        Args:
            product: Product to find related items for
            limit: Maximum number of related products
            
        Returns:
            List of related products
        """
        # Find products in same category, excluding the current product
        return self.session.query(Product).filter(
            and_(
                Product.category_id == product.category_id,
                Product.id != product.id,
                Product.status == ProductStatus.ACTIVE.value,
                Product.is_deleted != 'Y'
            )
        ).order_by(
            desc(Product.thumbs_up_count),
            desc(Product.view_count)
        ).limit(limit).all()
    
    def get_popular_products(self, limit: int = 10) -> List[Product]:
        """
        Get most popular products based on views and reviews
        
        Args:
            limit: Maximum number of products
            
        Returns:
            List of popular products
        """
        return self.session.query(Product).filter(
            and_(
                Product.status == ProductStatus.ACTIVE.value,
                Product.is_deleted != 'Y'
            )
        ).order_by(
            desc(Product.thumbs_up_count),
            desc(Product.view_count),
            desc(Product.download_count)
        ).limit(limit).all()
    
    def increment_view_count(self, product_id: int) -> bool:
        """
        Increment product view counter
        
        Args:
            product_id: Product ID
            
        Returns:
            True if successful
        """
        try:
            self.session.query(Product).filter(
                Product.id == product_id
            ).update({
                Product.view_count: Product.view_count + 1
            })
            return True
        except Exception:
            return False
    
    def increment_download_count(self, product_id: int) -> bool:
        """
        Increment product download counter
        
        Args:
            product_id: Product ID
            
        Returns:
            True if successful
        """
        try:
            self.session.query(Product).filter(
                Product.id == product_id
            ).update({
                Product.download_count: Product.download_count + 1
            })
            return True
        except Exception:
            return False
    
    def get_product_stats(self) -> Dict[str, Any]:
        """
        Get overall product statistics
        
        Returns:
            Dictionary with product statistics
        """
        try:
            total_products = self.session.query(func.count(Product.id)).scalar()
            active_products = self.session.query(func.count(Product.id)).filter(
                Product.status == ProductStatus.ACTIVE.value
            ).scalar()
            
            avg_price = self.session.query(func.avg(Product.price)).filter(
                and_(
                    Product.price.isnot(None),
                    Product.price_type == PriceType.FIXED.value
                )
            ).scalar()
            
            total_views = self.session.query(func.sum(Product.view_count)).scalar()
            total_downloads = self.session.query(func.sum(Product.download_count)).scalar()
            
            return {
                'total_products': total_products or 0,
                'active_products': active_products or 0,
                'average_price': float(avg_price) if avg_price else 0.0,
                'total_views': total_views or 0,
                'total_downloads': total_downloads or 0
            }
        except Exception:
            return {
                'total_products': 0,
                'active_products': 0,
                'average_price': 0.0,
                'total_views': 0,
                'total_downloads': 0
            }


class ProductCategoryRepository(BaseRepository[ProductCategory]):
    """Repository for ProductCategory entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(ProductCategory, session)
    
    def get_active_categories(self) -> List[ProductCategory]:
        """
        Get all active categories with product counts
        
        Returns:
            List of active categories
        """
        return self.session.query(ProductCategory).filter(
            ProductCategory.is_active == True
        ).order_by(
            ProductCategory.sort_order,
            ProductCategory.name
        ).all()
    
    def get_by_slug(self, slug: str) -> Optional[ProductCategory]:
        """
        Get category by URL slug
        
        Args:
            slug: URL-friendly category identifier
            
        Returns:
            ProductCategory instance or None
        """
        return self.session.query(ProductCategory).filter(
            ProductCategory.slug == slug
        ).first()
    
    def get_root_categories(self) -> List[ProductCategory]:
        """
        Get top-level categories (no parent)
        
        Returns:
            List of root categories
        """
        return self.session.query(ProductCategory).filter(
            and_(
                ProductCategory.parent_id.is_(None),
                ProductCategory.is_active == True
            )
        ).order_by(
            ProductCategory.sort_order,
            ProductCategory.name
        ).all()
    
    def get_category_tree(self) -> List[Dict[str, Any]]:
        """
        Get hierarchical category tree
        
        Returns:
            List of categories with nested children
        """
        categories = self.get_active_categories()
        category_map = {cat.id: cat.to_dict() for cat in categories}
        
        # Add children lists
        for cat_data in category_map.values():
            cat_data['children'] = []
        
        # Build tree structure
        root_categories = []
        for category in categories:
            cat_data = category_map[category.id]
            
            if category.parent_id and category.parent_id in category_map:
                # Add to parent's children
                category_map[category.parent_id]['children'].append(cat_data)
            else:
                # Root category
                root_categories.append(cat_data)
        
        return root_categories


class ProductReviewRepository(BaseRepository[ProductReview]):
    """Repository for ProductReview entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(ProductReview, session)
    
    def add_thumbs_up(self, product_id: int, customer_ip: str = None, 
                     validation_answer: str = None, customer_id: int = None) -> ProductReview:
        """
        Add a thumbs up review for a product
        
        Args:
            product_id: Product ID
            customer_ip: Customer IP address for spam prevention
            validation_answer: Human validation answer
            customer_id: Optional customer ID if logged in
            
        Returns:
            Created review instance
        """
        review = ProductReview(
            product_id=product_id,
            customer_ip=customer_ip,
            validation_answer=validation_answer,
            customer_id=customer_id
        )
        
        created_review = self.create(review)
        
        # Update product thumbs up count
        self.session.query(Product).filter(
            Product.id == product_id
        ).update({
            Product.thumbs_up_count: Product.thumbs_up_count + 1
        })
        
        return created_review
    
    def get_product_thumbs_up_count(self, product_id: int) -> int:
        """
        Get thumbs up count for a product
        
        Args:
            product_id: Product ID
            
        Returns:
            Number of thumbs up reviews
        """
        return self.session.query(func.count(ProductReview.id)).filter(
            ProductReview.product_id == product_id
        ).scalar() or 0
    
    def check_customer_already_reviewed(self, product_id: int, 
                                       customer_ip: str = None, 
                                       customer_id: int = None) -> bool:
        """
        Check if customer has already reviewed this product
        
        Args:
            product_id: Product ID
            customer_ip: Customer IP address
            customer_id: Customer ID if logged in
            
        Returns:
            True if customer has already reviewed
        """
        conditions = [ProductReview.product_id == product_id]
        
        if customer_id:
            conditions.append(ProductReview.customer_id == customer_id)
        elif customer_ip:
            conditions.append(ProductReview.customer_ip == customer_ip)
        else:
            return False
        
        return self.session.query(ProductReview).filter(
            and_(*conditions)
        ).first() is not None


class ProductInquiryRepository(BaseRepository[ProductInquiry]):
    """Repository for ProductInquiry entities"""
    
    def __init__(self, session: Session = None):
        super().__init__(ProductInquiry, session)
    
    def create_inquiry(self, product_id: int, customer_email: str, 
                      question: str, customer_name: str = None,
                      customer_ip: str = None, validation_answer: str = None,
                      customer_id: int = None) -> ProductInquiry:
        """
        Create a product inquiry
        
        Args:
            product_id: Product ID
            customer_email: Customer email address
            question: Customer question
            customer_name: Customer name
            customer_ip: Customer IP address
            validation_answer: Human validation answer
            customer_id: Customer ID if logged in
            
        Returns:
            Created inquiry instance
        """
        inquiry = ProductInquiry(
            product_id=product_id,
            customer_email=customer_email,
            customer_name=customer_name,
            question=question,
            customer_ip=customer_ip,
            validation_answer=validation_answer,
            customer_id=customer_id
        )
        
        return self.create(inquiry)
    
    def get_product_inquiries(self, product_id: int, 
                             status: str = None) -> List[ProductInquiry]:
        """
        Get inquiries for a specific product
        
        Args:
            product_id: Product ID
            status: Optional status filter
            
        Returns:
            List of product inquiries
        """
        query = self.session.query(ProductInquiry).filter(
            ProductInquiry.product_id == product_id
        )
        
        if status:
            query = query.filter(ProductInquiry.status == status)
        
        return query.order_by(desc(ProductInquiry.created_at)).all()
    
    def get_pending_inquiries(self) -> List[ProductInquiry]:
        """
        Get all pending inquiries for admin review
        
        Returns:
            List of pending inquiries
        """
        return self.session.query(ProductInquiry).filter(
            ProductInquiry.status == 'pending'
        ).order_by(ProductInquiry.created_at).all()
    
    def mark_as_responded(self, inquiry_id: int, admin_response: str) -> bool:
        """
        Mark inquiry as responded
        
        Args:
            inquiry_id: Inquiry ID
            admin_response: Admin response text
            
        Returns:
            True if successful
        """
        try:
            from datetime import datetime
            self.session.query(ProductInquiry).filter(
                ProductInquiry.id == inquiry_id
            ).update({
                ProductInquiry.status: 'responded',
                ProductInquiry.admin_response: admin_response,
                ProductInquiry.responded_at: datetime.utcnow()
            })
            return True
        except Exception:
            return False