"""
Webshop Repositories Package - Data access layer for the AgentShop webshop
Contains all repository classes organized by functional area
"""

# Base repository
from .base_repository import (
    BaseRepository,
    UnitOfWork,
    RepositoryError
)

# Product repositories
from .product_repository import (
    ProductRepository,
    ProductCategoryRepository,
    ProductReviewRepository,
    ProductInquiryRepository
)

# Customer repositories
from .customer_repository import (
    CustomerRepository,
    CustomerSessionRepository,
    SupportRequestRepository
)

# Order repositories
from .order_repository import (
    OrderRepository,
    OrderItemRepository,
    PaymentRepository,
    InstallationRequestRepository
)

# Admin repositories
from .admin_repository import (
    AdminUserRepository,
    AdminSessionRepository,
    ConfigSettingRepository,
    EmailTemplateRepository,
    create_default_admin_user
)

__all__ = [
    # Base repository
    'BaseRepository',
    'UnitOfWork',
    'RepositoryError',
    
    # Product repositories
    'ProductRepository',
    'ProductCategoryRepository',
    'ProductReviewRepository',
    'ProductInquiryRepository',
    
    # Customer repositories
    'CustomerRepository',
    'CustomerSessionRepository',
    'SupportRequestRepository',
    
    # Order repositories
    'OrderRepository',
    'OrderItemRepository',
    'PaymentRepository',
    'InstallationRequestRepository',
    
    # Admin repositories
    'AdminUserRepository',
    'AdminSessionRepository',
    'ConfigSettingRepository',
    'EmailTemplateRepository',
    'create_default_admin_user'
]