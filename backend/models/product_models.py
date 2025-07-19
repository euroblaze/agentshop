#!/usr/bin/env python3
"""
Product Models - Database models for product management
Handles AI agent software products, categories, and related functionality
"""

from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from typing import Dict, Any, List, Optional
import json
from enum import Enum

from core.orm.base_model import BaseModel, SoftDeleteMixin


class PriceType(Enum):
    """Enumeration for product pricing types"""
    FIXED = "fixed"           # Fixed price with buy button
    INQUIRY = "inquiry"       # Price on inquiry via email
    FREE = "free"            # Free product
    SUBSCRIPTION = "subscription"  # Recurring subscription


class ProductStatus(Enum):
    """Enumeration for product status"""
    DRAFT = "draft"          # Not yet published
    ACTIVE = "active"        # Available for purchase
    INACTIVE = "inactive"    # Temporarily unavailable
    ARCHIVED = "archived"    # No longer available


class Product(BaseModel, SoftDeleteMixin):
    """AI Agent Software Product Model"""
    
    __tablename__ = 'products'
    
    # Basic product information
    name = Column(String(200), nullable=False, index=True)
    title = Column(String(300), nullable=False)  # SEO-optimized title
    slug = Column(String(200), nullable=False, unique=True, index=True)  # URL-friendly name
    
    # Descriptions and content
    short_description = Column(Text, nullable=False)  # Brief summary
    full_description = Column(Text, nullable=False)   # Detailed description
    html_content = Column(Text)                       # Rich HTML content for product page
    
    # Pricing and availability
    price = Column(Float, nullable=True)              # Price in USD (null for inquiry)
    price_type = Column(String(20), nullable=False, default=PriceType.FIXED.value)
    currency = Column(String(3), nullable=False, default='USD')
    
    # Product status and categorization
    status = Column(String(20), nullable=False, default=ProductStatus.DRAFT.value)
    category_id = Column(Integer, ForeignKey('product_categories.id'), nullable=True)
    
    # Resources and downloads
    readme_link = Column(String(500))                 # Link to README file
    download_link = Column(String(500))               # Secure download link
    demo_url = Column(String(500))                    # Demo or preview URL
    documentation_url = Column(String(500))           # Documentation link
    
    # SEO and marketing
    meta_title = Column(String(300))                  # SEO meta title
    meta_description = Column(String(500))            # SEO meta description
    keywords = Column(Text)                           # SEO keywords (comma-separated)
    
    # Product metrics
    download_count = Column(Integer, default=0)       # Number of downloads
    view_count = Column(Integer, default=0)           # Number of page views
    thumbs_up_count = Column(Integer, default=0)      # Positive reviews count
    
    # Technical specifications
    system_requirements = Column(Text)                # System requirements
    version = Column(String(50))                      # Current version
    license_type = Column(String(100))                # Software license
    
    # Images and media
    featured_image = Column(String(500))              # Main product image
    gallery_images = Column(Text)                     # JSON array of image URLs
    video_url = Column(String(500))                   # Product demo video
    
    # Relationships
    category = relationship("ProductCategory", back_populates="products")
    reviews = relationship("ProductReview", back_populates="product", cascade="all, delete-orphan")
    inquiries = relationship("ProductInquiry", back_populates="product", cascade="all, delete-orphan")
    order_items = relationship("OrderItem", back_populates="product")
    
    def __init__(self, **kwargs):
        """Initialize product with validation"""
        super().__init__()
        
        # Set default values
        if 'price_type' not in kwargs:
            kwargs['price_type'] = PriceType.FIXED.value
        if 'status' not in kwargs:
            kwargs['status'] = ProductStatus.DRAFT.value
        if 'currency' not in kwargs:
            kwargs['currency'] = 'USD'
        
        # Generate slug from name if not provided
        if 'slug' not in kwargs and 'name' in kwargs:
            kwargs['slug'] = self._generate_slug(kwargs['name'])
        
        # Set attributes
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from product name"""
        import re
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug.strip('-')
    
    @property
    def is_purchasable(self) -> bool:
        """Check if product can be purchased directly"""
        return (
            self.status == ProductStatus.ACTIVE.value and
            self.price_type in [PriceType.FIXED.value, PriceType.FREE.value] and
            not self.is_deleted
        )
    
    @property
    def is_inquiry_only(self) -> bool:
        """Check if product requires price inquiry"""
        return self.price_type == PriceType.INQUIRY.value
    
    @property
    def display_price(self) -> str:
        """Get formatted price for display"""
        if self.price_type == PriceType.FREE.value:
            return "Free"
        elif self.price_type == PriceType.INQUIRY.value:
            return "Price on Request"
        elif self.price is not None:
            return f"${self.price:.2f}"
        else:
            return "Price not set"
    
    def get_gallery_images(self) -> List[str]:
        """Get list of gallery image URLs"""
        if self.gallery_images:
            try:
                return json.loads(self.gallery_images)
            except json.JSONDecodeError:
                return []
        return []
    
    def set_gallery_images(self, image_urls: List[str]):
        """Set gallery images from list of URLs"""
        self.gallery_images = json.dumps(image_urls)
    
    def get_keywords_list(self) -> List[str]:
        """Get list of keywords"""
        if self.keywords:
            return [kw.strip() for kw in self.keywords.split(',') if kw.strip()]
        return []
    
    def set_keywords_list(self, keywords: List[str]):
        """Set keywords from list"""
        self.keywords = ', '.join(keywords)
    
    def increment_view_count(self):
        """Increment the product view counter"""
        self.view_count = (self.view_count or 0) + 1
    
    def increment_download_count(self):
        """Increment the download counter"""
        self.download_count = (self.download_count or 0) + 1
    
    def add_thumbs_up(self):
        """Add a thumbs up review"""
        self.thumbs_up_count = (self.thumbs_up_count or 0) + 1
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate product data"""
        errors = super().validate()
        
        # Validate price based on price type
        if self.price_type == PriceType.FIXED.value and self.price is None:
            if 'price' not in errors:
                errors['price'] = []
            errors['price'].append("Price is required for fixed price products")
        
        # Validate slug uniqueness (would need database check in real implementation)
        if not self.slug:
            if 'slug' not in errors:
                errors['slug'] = []
            errors['slug'].append("Slug is required")
        
        # Validate URL formats
        url_fields = ['readme_link', 'download_link', 'demo_url', 'documentation_url', 'video_url']
        for field in url_fields:
            value = getattr(self, field)
            if value and not self._is_valid_url(value):
                if field not in errors:
                    errors[field] = []
                errors[field].append(f"Invalid URL format for {field}")
        
        return errors
    
    def _is_valid_url(self, url: str) -> bool:
        """Basic URL validation"""
        import re
        pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        return pattern.match(url) is not None
    
    def to_dict(self, exclude_fields: List[str] = None) -> Dict[str, Any]:
        """Convert to dictionary with additional computed fields"""
        data = super().to_dict(exclude_fields)
        data.update({
            'is_purchasable': self.is_purchasable,
            'is_inquiry_only': self.is_inquiry_only,
            'display_price': self.display_price,
            'gallery_images_list': self.get_gallery_images(),
            'keywords_list': self.get_keywords_list(),
        })
        return data


class ProductCategory(BaseModel):
    """Product categories for organization and navigation"""
    
    __tablename__ = 'product_categories'
    
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(100), nullable=False, unique=True, index=True)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey('product_categories.id'), nullable=True)
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # SEO fields
    meta_title = Column(String(300))
    meta_description = Column(String(500))
    
    # Relationships
    parent = relationship("ProductCategory", remote_side="ProductCategory.id", back_populates="children")
    children = relationship("ProductCategory", back_populates="parent")
    products = relationship("Product", back_populates="category")
    
    def __init__(self, **kwargs):
        super().__init__()
        
        # Generate slug from name if not provided
        if 'slug' not in kwargs and 'name' in kwargs:
            kwargs['slug'] = self._generate_slug(kwargs['name'])
        
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from category name"""
        import re
        slug = re.sub(r'[^\w\s-]', '', name.lower())
        slug = re.sub(r'[\s_-]+', '-', slug)
        return slug.strip('-')
    
    @property
    def full_path(self) -> str:
        """Get full category path including parent categories"""
        if self.parent:
            return f"{self.parent.full_path} > {self.name}"
        return self.name
    
    def get_active_products_count(self) -> int:
        """Get count of active products in this category"""
        return len([p for p in self.products if p.status == ProductStatus.ACTIVE.value and not p.is_deleted])


class ProductReview(BaseModel):
    """Simple thumbs-up reviews for products"""
    
    __tablename__ = 'product_reviews'
    
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    customer_ip = Column(String(45))  # Store IP to prevent spam (IPv6 support)
    user_agent = Column(String(500))  # Browser info for spam detection
    validation_answer = Column(String(100))  # Answer to human validation question
    
    # Optional customer info (if logged in)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="reviews")
    customer = relationship("Customer", back_populates="reviews")
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate review data"""
        errors = super().validate()
        
        if not self.validation_answer:
            if 'validation_answer' not in errors:
                errors['validation_answer'] = []
            errors['validation_answer'].append("Human validation is required")
        
        return errors


class ProductInquiry(BaseModel):
    """Customer inquiries about products"""
    
    __tablename__ = 'product_inquiries'
    
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False, index=True)
    customer_email = Column(String(255), nullable=False)
    customer_name = Column(String(200))
    question = Column(Text, nullable=False)
    
    # Spam prevention
    customer_ip = Column(String(45))
    user_agent = Column(String(500))
    validation_answer = Column(String(100))
    
    # Status tracking
    status = Column(String(20), default='pending')  # pending, responded, closed
    admin_response = Column(Text)
    responded_at = Column(DateTime)
    
    # Optional customer relationship
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="inquiries")
    customer = relationship("Customer", back_populates="inquiries")
    
    def validate(self) -> Dict[str, List[str]]:
        """Validate inquiry data"""
        errors = super().validate()
        
        # Email validation
        if self.customer_email and not self._is_valid_email(self.customer_email):
            if 'customer_email' not in errors:
                errors['customer_email'] = []
            errors['customer_email'].append("Invalid email format")
        
        return errors
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None


# Import references for relationships
from .customer_models import Customer