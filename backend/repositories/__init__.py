"""
AgentShop Repositories Package - All data access layers for AgentShop

Contains all repository classes organized by functional area:
- Base repository functionality from core
- LLM repositories (AI/ML data access)
- Webshop repositories (products, orders, customers, admin)
"""

# Base repository from core
from core.repositories.base_repository import (
    BaseRepository,
    RepositoryError
)
from core.repositories.unit_of_work import UnitOfWork

# LLM repositories
from .llm_repository import (
    LLMRequestRepository,
    LLMResponseRepository,
    LLMConversationRepository,
    LLMConversationMessageRepository,
    LLMUsageStatsRepository,
    LLMProviderStatusRepository
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
    
    # LLM repositories
    'LLMRequestRepository',
    'LLMResponseRepository',
    'LLMConversationRepository',
    'LLMConversationMessageRepository',
    'LLMUsageStatsRepository',
    'LLMProviderStatusRepository',
    
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