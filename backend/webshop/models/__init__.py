"""
Webshop Models Package - Domain models for the AgentShop webshop
Contains all database models organized by functional area
"""

# Product models
from .product_models import (
    Product,
    ProductCategory,
    ProductReview,
    ProductInquiry,
    PriceType,
    ProductStatus
)

# Customer models
from .customer_models import (
    Customer,
    CustomerSession,
    SupportRequest
)

# Order models
from .order_models import (
    Order,
    OrderItem,
    Payment,
    InstallationRequest,
    OrderStatus,
    PaymentStatus,
    PaymentProcessor
)

# Admin models
from .admin_models import (
    AdminUser,
    AdminSession,
    ConfigSetting,
    EmailTemplate,
    create_default_settings,
    DEFAULT_CONFIG_SETTINGS
)

# Base ORM imports
from ..orm.base_model import (
    BaseModel,
    Base,
    get_db_session,
    create_all_tables
)

__all__ = [
    # Product models
    'Product',
    'ProductCategory', 
    'ProductReview',
    'ProductInquiry',
    'PriceType',
    'ProductStatus',
    
    # Customer models
    'Customer',
    'CustomerSession',
    'SupportRequest',
    
    # Order models
    'Order',
    'OrderItem',
    'Payment',
    'InstallationRequest',
    'OrderStatus',
    'PaymentStatus',
    'PaymentProcessor',
    
    # Admin models
    'AdminUser',
    'AdminSession',
    'ConfigSetting',
    'EmailTemplate',
    'create_default_settings',
    'DEFAULT_CONFIG_SETTINGS',
    
    # Base ORM
    'BaseModel',
    'Base',
    'get_db_session',
    'create_all_tables'
]