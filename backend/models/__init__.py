"""
AgentShop Models Package - All domain models for AgentShop

Contains all database models organized by functional area:
- LLM models (AI/ML functionality)
- Webshop models (products, orders, customers, admin)
"""

# LLM models
from .llm_models import (
    LLMRequest,
    LLMResponse, 
    LLMConversation,
    LLMConversationMessage,
    LLMUsageStats,
    LLMProviderStatus
)

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

# Base ORM imports from core
from core.orm.base_model import (
    BaseModel,
    Base
)
from core.orm.database import (
    get_db_session,
    create_all_tables
)

__all__ = [
    # LLM models
    'LLMRequest',
    'LLMResponse', 
    'LLMConversation',
    'LLMConversationMessage',
    'LLMUsageStats',
    'LLMProviderStatus',
    
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