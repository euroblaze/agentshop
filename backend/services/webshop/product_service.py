#!/usr/bin/env python3
"""
Product Service - Business logic for product management
Handles products, categories, reviews, and inquiries with comprehensive business rules
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import logging

from .base_service import BaseService, ValidationError, ServiceError
from ..repositories.product_repository import (
    ProductRepository, ProductCategoryRepository, 
    ProductReviewRepository, ProductInquiryRepository
)
from ..models.product_models import (
    Product, ProductCategory, ProductReview, ProductInquiry,
    ProductStatus, PriceType
)

logger = logging.getLogger(__name__)


class ProductService(BaseService[Product]):
    """Service for Product entity with specialized business logic"""
    
    def __init__(self, repository: ProductRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> ProductRepository:
        """Create ProductRepository instance"""
        return ProductRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> Product:
        """Create Product instance from data dictionary"""
        return Product(**entity_data)
    
    def _validate_business_rules(self, product: Product, 
                                is_create: bool = True) -> Dict[str, List[str]]:
        """Validate product business rules"""
        errors = {}
        
        # Validate slug uniqueness
        if is_create or product.slug:
            existing_product = self.repository.get_by_slug(product.slug)
            if existing_product and existing_product.id != product.id:
                errors['slug'] = ['Slug already exists']
        
        # Validate price based on price type
        if product.price_type == PriceType.FIXED.value:
            if product.price is None or product.price <= 0:
                errors['price'] = ['Price must be greater than 0 for fixed price products']
        elif product.price_type == PriceType.FREE.value:
            if product.price is not None and product.price != 0:
                errors['price'] = ['Price must be 0 for free products']
        
        # Validate required fields for active products
        if product.status == ProductStatus.ACTIVE.value:
            required_fields = {
                'short_description': 'Short description is required for active products',
                'full_description': 'Full description is required for active products',
                'category_id': 'Category is required for active products'
            }
            
            for field, message in required_fields.items():
                value = getattr(product, field)
                if not value or (isinstance(value, str) and not value.strip()):
                    if field not in errors:
                        errors[field] = []
                    errors[field].append(message)
        
        return errors
    
    def _apply_create_business_rules(self, product: Product, entity_data: Dict[str, Any]):
        """Apply business rules during product creation"""
        # Generate slug if not provided
        if not product.slug and product.name:
            product.slug = self._generate_unique_slug(product.name)
        
        # Set default status
        if not product.status:
            product.status = ProductStatus.DRAFT.value
        
        # Initialize counters
        product.view_count = 0
        product.download_count = 0
        product.thumbs_up_count = 0
    
    def _apply_update_business_rules(self, product: Product,
                                   update_data: Dict[str, Any],
                                   original_product: Product):
        """Apply business rules during product update"""
        # Regenerate slug if name changed
        if 'name' in update_data and product.name != original_product.name:
            if not update_data.get('slug'):
                product.slug = self._generate_unique_slug(product.name)
        
        # Handle status changes
        if product.status != original_product.status:
            self._handle_status_change(product, original_product.status)
    
    def _can_delete(self, product: Product) -> bool:
        """Check if product can be deleted"""
        # Check if product has orders
        from ..repositories.order_repository import OrderItemRepository
        order_item_repo = OrderItemRepository(self.session)
        order_items = order_item_repo.find_by(product_id=product.id)
        
        if order_items:
            return False  # Cannot delete products with orders
        
        return True
    
    def _get_default_filters(self) -> Dict[str, Any]:
        """Get default filters for product queries"""
        return {'is_deleted': 'N'}
    
    def _get_default_search_fields(self) -> List[str]:
        """Get default search fields for products"""
        return ['name', 'title', 'short_description', 'keywords']
    
    # Public business methods
    
    def get_active_products(self, category_id: int = None, 
                           limit: int = None, offset: int = None) -> List[Product]:
        """
        Get active products with optional category filter
        
        Args:
            category_id: Optional category filter
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of active products
        """
        try:
            return self.repository.get_active_products(limit, offset, category_id)
        except Exception as e:
            logger.error(f"Error getting active products: {e}")
            return []
    
    def get_featured_products(self, limit: int = 6) -> List[Product]:
        """
        Get featured products for homepage
        
        Args:
            limit: Maximum number of featured products
            
        Returns:
            List of featured products
        """
        try:
            return self.repository.get_featured_products(limit)
        except Exception as e:
            logger.error(f"Error getting featured products: {e}")
            return []
    
    def get_by_slug(self, slug: str) -> Optional[Product]:
        """
        Get product by URL slug and increment view count
        
        Args:
            slug: Product URL slug
            
        Returns:
            Product instance or None
        """
        try:
            product = self.repository.get_by_slug(slug)
            if product:
                # Increment view count
                self.repository.increment_view_count(product.id)
                product.view_count = (product.view_count or 0) + 1
            return product
        except Exception as e:
            logger.error(f"Error getting product by slug: {e}")
            return None
    
    def search_products(self, search_term: str = None, category_id: int = None,
                       price_type: str = None, min_price: float = None,
                       max_price: float = None, limit: int = 50,
                       offset: int = None) -> List[Product]:
        """
        Search products with multiple filters
        
        Args:
            search_term: Text to search for
            category_id: Category filter
            price_type: Price type filter
            min_price: Minimum price filter
            max_price: Maximum price filter
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of matching products
        """
        try:
            return self.repository.search_products(
                search_term, category_id, price_type,
                min_price, max_price, limit, offset
            )
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    def get_related_products(self, product: Product, limit: int = 4) -> List[Product]:
        """
        Get products related to the given product
        
        Args:
            product: Product to find related items for
            limit: Maximum number of related products
            
        Returns:
            List of related products
        """
        try:
            return self.repository.get_related_products(product, limit)
        except Exception as e:
            logger.error(f"Error getting related products: {e}")
            return []
    
    def publish_product(self, product_id: int) -> bool:
        """
        Publish a product (change status to active)
        
        Args:
            product_id: Product ID
            
        Returns:
            True if successful
        """
        try:
            product = self.get_by_id(product_id)
            if not product:
                return False
            
            # Validate product is ready for publishing
            validation_errors = self._validate_for_publishing(product)
            if validation_errors:
                raise ValidationError("Product not ready for publishing", validation_errors)
            
            # Update status
            product.status = ProductStatus.ACTIVE.value
            self.repository.update(product)
            
            return True
        except Exception as e:
            logger.error(f"Error publishing product: {e}")
            return False
    
    def unpublish_product(self, product_id: int) -> bool:
        """
        Unpublish a product (change status to inactive)
        
        Args:
            product_id: Product ID
            
        Returns:
            True if successful
        """
        try:
            product = self.get_by_id(product_id)
            if not product:
                return False
            
            product.status = ProductStatus.INACTIVE.value
            self.repository.update(product)
            
            return True
        except Exception as e:
            logger.error(f"Error unpublishing product: {e}")
            return False
    
    def record_download(self, product_id: int) -> bool:
        """
        Record a product download
        
        Args:
            product_id: Product ID
            
        Returns:
            True if successful
        """
        try:
            return self.repository.increment_download_count(product_id)
        except Exception as e:
            logger.error(f"Error recording download: {e}")
            return False
    
    def get_product_stats(self) -> Dict[str, Any]:
        """
        Get product statistics
        
        Returns:
            Dictionary with product statistics
        """
        try:
            return self.repository.get_product_stats()
        except Exception as e:
            logger.error(f"Error getting product stats: {e}")
            return {}
    
    # Helper methods
    
    def _generate_unique_slug(self, name: str) -> str:
        """Generate unique slug from product name"""
        import re
        
        base_slug = re.sub(r'[^\w\s-]', '', name.lower())
        base_slug = re.sub(r'[\s_-]+', '-', base_slug).strip('-')
        
        slug = base_slug
        counter = 1
        
        while self.repository.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    def _handle_status_change(self, product: Product, old_status: str):
        """Handle product status changes"""
        if product.status == ProductStatus.ACTIVE.value and old_status != ProductStatus.ACTIVE.value:
            # Product being published
            logger.info(f"Product {product.id} published")
        elif old_status == ProductStatus.ACTIVE.value and product.status != ProductStatus.ACTIVE.value:
            # Product being unpublished
            logger.info(f"Product {product.id} unpublished")
    
    def _validate_for_publishing(self, product: Product) -> Dict[str, List[str]]:
        """Validate product is ready for publishing"""
        errors = {}
        
        required_fields = {
            'short_description': 'Short description required',
            'full_description': 'Full description required',
            'category_id': 'Category required'
        }
        
        for field, message in required_fields.items():
            value = getattr(product, field)
            if not value or (isinstance(value, str) and not value.strip()):
                if field not in errors:
                    errors[field] = []
                errors[field].append(message)
        
        # Check price requirements
        if product.price_type == PriceType.FIXED.value and (not product.price or product.price <= 0):
            if 'price' not in errors:
                errors['price'] = []
            errors['price'].append("Price required for fixed price products")
        
        return errors


class ProductCategoryService(BaseService[ProductCategory]):
    """Service for ProductCategory entity"""
    
    def __init__(self, repository: ProductCategoryRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> ProductCategoryRepository:
        """Create ProductCategoryRepository instance"""
        return ProductCategoryRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> ProductCategory:
        """Create ProductCategory instance from data dictionary"""
        return ProductCategory(**entity_data)
    
    def _validate_business_rules(self, category: ProductCategory,
                                is_create: bool = True) -> Dict[str, List[str]]:
        """Validate category business rules"""
        errors = {}
        
        # Validate slug uniqueness
        if is_create or category.slug:
            existing_category = self.repository.get_by_slug(category.slug)
            if existing_category and existing_category.id != category.id:
                errors['slug'] = ['Slug already exists']
        
        # Validate parent category exists and is not self
        if category.parent_id:
            if category.parent_id == category.id:
                errors['parent_id'] = ['Category cannot be its own parent']
            else:
                parent = self.repository.get_by_id(category.parent_id)
                if not parent:
                    errors['parent_id'] = ['Parent category does not exist']
        
        return errors
    
    def _apply_create_business_rules(self, category: ProductCategory, entity_data: Dict[str, Any]):
        """Apply business rules during category creation"""
        # Generate slug if not provided
        if not category.slug and category.name:
            category.slug = self._generate_unique_slug(category.name)
        
        # Set default sort order
        if category.sort_order is None:
            category.sort_order = 0
    
    def _can_delete(self, category: ProductCategory) -> bool:
        """Check if category can be deleted"""
        # Check if category has products
        from ..repositories.product_repository import ProductRepository
        product_repo = ProductRepository(self.session)
        products = product_repo.find_by(category_id=category.id)
        
        if products:
            return False  # Cannot delete categories with products
        
        # Check if category has child categories
        child_categories = self.repository.find_by(parent_id=category.id)
        if child_categories:
            return False  # Cannot delete categories with children
        
        return True
    
    def _get_default_search_fields(self) -> List[str]:
        """Get default search fields for categories"""
        return ['name', 'description']
    
    # Public business methods
    
    def get_active_categories(self) -> List[ProductCategory]:
        """Get all active categories"""
        try:
            return self.repository.get_active_categories()
        except Exception as e:
            logger.error(f"Error getting active categories: {e}")
            return []
    
    def get_by_slug(self, slug: str) -> Optional[ProductCategory]:
        """Get category by URL slug"""
        try:
            return self.repository.get_by_slug(slug)
        except Exception as e:
            logger.error(f"Error getting category by slug: {e}")
            return None
    
    def get_category_tree(self) -> List[Dict[str, Any]]:
        """Get hierarchical category tree"""
        try:
            return self.repository.get_category_tree()
        except Exception as e:
            logger.error(f"Error getting category tree: {e}")
            return []
    
    def get_root_categories(self) -> List[ProductCategory]:
        """Get top-level categories"""
        try:
            return self.repository.get_root_categories()
        except Exception as e:
            logger.error(f"Error getting root categories: {e}")
            return []
    
    def _generate_unique_slug(self, name: str) -> str:
        """Generate unique slug from category name"""
        import re
        
        base_slug = re.sub(r'[^\w\s-]', '', name.lower())
        base_slug = re.sub(r'[\s_-]+', '-', base_slug).strip('-')
        
        slug = base_slug
        counter = 1
        
        while self.repository.get_by_slug(slug):
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug


class ProductReviewService(BaseService[ProductReview]):
    """Service for ProductReview entity"""
    
    def __init__(self, repository: ProductReviewRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> ProductReviewRepository:
        """Create ProductReviewRepository instance"""
        return ProductReviewRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> ProductReview:
        """Create ProductReview instance from data dictionary"""
        return ProductReview(**entity_data)
    
    def _validate_business_rules(self, review: ProductReview,
                                is_create: bool = True) -> Dict[str, List[str]]:
        """Validate review business rules"""
        errors = {}
        
        # Check if customer already reviewed this product
        if is_create:
            already_reviewed = self.repository.check_customer_already_reviewed(
                review.product_id, review.customer_ip, review.customer_id
            )
            if already_reviewed:
                errors['product_id'] = ['You have already reviewed this product']
        
        # Validate product exists
        from ..repositories.product_repository import ProductRepository
        product_repo = ProductRepository(self.session)
        product = product_repo.get_by_id(review.product_id)
        if not product:
            errors['product_id'] = ['Product does not exist']
        elif product.status != ProductStatus.ACTIVE.value:
            errors['product_id'] = ['Cannot review inactive product']
        
        return errors
    
    # Public business methods
    
    def add_thumbs_up(self, product_id: int, validation_answer: str,
                     customer_ip: str = None, customer_id: int = None) -> bool:
        """
        Add thumbs up review for a product
        
        Args:
            product_id: Product ID
            validation_answer: Human validation answer
            customer_ip: Customer IP address
            customer_id: Customer ID if logged in
            
        Returns:
            True if successful
        """
        try:
            # Validate human verification (simple example)
            if not self._validate_human_verification(validation_answer):
                raise ValidationError("Human verification failed", 
                                    {'validation_answer': ['Incorrect answer']})
            
            # Create review
            review = self.repository.add_thumbs_up(
                product_id, customer_ip, validation_answer, customer_id
            )
            
            return review is not None
        except Exception as e:
            logger.error(f"Error adding thumbs up: {e}")
            return False
    
    def get_product_thumbs_up_count(self, product_id: int) -> int:
        """Get thumbs up count for a product"""
        try:
            return self.repository.get_product_thumbs_up_count(product_id)
        except Exception as e:
            logger.error(f"Error getting thumbs up count: {e}")
            return 0
    
    def _validate_human_verification(self, answer: str) -> bool:
        """Validate human verification answer (simple implementation)"""
        # Simple example - in real implementation, this would be more sophisticated
        valid_answers = ['human', 'yes', 'verified']
        return answer.lower() in valid_answers


class ProductInquiryService(BaseService[ProductInquiry]):
    """Service for ProductInquiry entity"""
    
    def __init__(self, repository: ProductInquiryRepository = None, session: Session = None):
        super().__init__(repository, session)
    
    def _create_repository(self) -> ProductInquiryRepository:
        """Create ProductInquiryRepository instance"""
        return ProductInquiryRepository(self._session)
    
    def _create_entity_from_data(self, entity_data: Dict[str, Any]) -> ProductInquiry:
        """Create ProductInquiry instance from data dictionary"""
        return ProductInquiry(**entity_data)
    
    def _validate_business_rules(self, inquiry: ProductInquiry,
                                is_create: bool = True) -> Dict[str, List[str]]:
        """Validate inquiry business rules"""
        errors = {}
        
        # Validate product exists
        from ..repositories.product_repository import ProductRepository
        product_repo = ProductRepository(self.session)
        product = product_repo.get_by_id(inquiry.product_id)
        if not product:
            errors['product_id'] = ['Product does not exist']
        elif product.status != ProductStatus.ACTIVE.value:
            errors['product_id'] = ['Cannot inquire about inactive product']
        
        return errors
    
    def _after_create(self, inquiry: ProductInquiry, entity_data: Dict[str, Any]):
        """Send notification email after inquiry creation"""
        try:
            # TODO: Implement email notification to admin
            logger.info(f"New product inquiry created: {inquiry.id}")
        except Exception as e:
            logger.error(f"Error sending inquiry notification: {e}")
    
    # Public business methods
    
    def create_inquiry(self, product_id: int, customer_email: str,
                      question: str, customer_name: str = None,
                      validation_answer: str = None,
                      customer_ip: str = None, customer_id: int = None) -> Optional[ProductInquiry]:
        """
        Create product inquiry with validation
        
        Args:
            product_id: Product ID
            customer_email: Customer email
            question: Customer question
            customer_name: Customer name
            validation_answer: Human validation answer
            customer_ip: Customer IP address
            customer_id: Customer ID if logged in
            
        Returns:
            Created inquiry or None
        """
        try:
            # Validate human verification
            if validation_answer and not self._validate_human_verification(validation_answer):
                raise ValidationError("Human verification failed",
                                    {'validation_answer': ['Incorrect answer']})
            
            inquiry_data = {
                'product_id': product_id,
                'customer_email': customer_email,
                'customer_name': customer_name,
                'question': question,
                'customer_ip': customer_ip,
                'validation_answer': validation_answer,
                'customer_id': customer_id
            }
            
            return self.create(inquiry_data)
        except Exception as e:
            logger.error(f"Error creating inquiry: {e}")
            return None
    
    def get_product_inquiries(self, product_id: int, status: str = None) -> List[ProductInquiry]:
        """Get inquiries for a product"""
        try:
            return self.repository.get_product_inquiries(product_id, status)
        except Exception as e:
            logger.error(f"Error getting product inquiries: {e}")
            return []
    
    def get_pending_inquiries(self) -> List[ProductInquiry]:
        """Get all pending inquiries for admin review"""
        try:
            return self.repository.get_pending_inquiries()
        except Exception as e:
            logger.error(f"Error getting pending inquiries: {e}")
            return []
    
    def respond_to_inquiry(self, inquiry_id: int, admin_response: str) -> bool:
        """Mark inquiry as responded with admin response"""
        try:
            return self.repository.mark_as_responded(inquiry_id, admin_response)
        except Exception as e:
            logger.error(f"Error responding to inquiry: {e}")
            return False
    
    def _validate_human_verification(self, answer: str) -> bool:
        """Validate human verification answer"""
        valid_answers = ['human', 'yes', 'verified']
        return answer.lower() in valid_answers