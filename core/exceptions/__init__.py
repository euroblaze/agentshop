"""
Core Exception Module

Provides unified exception handling across all AgentShop modules.
Combines the best features from webshop and backend exception implementations.
"""

from .base_exceptions import (
    AgentShopError,
    APIError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    RateLimitError,
    ServerError,
    BusinessLogicError,
    ExternalServiceError
)

from .auth_exceptions import (
    TokenExpiredError,
    InvalidTokenError,
    TokenRequiredError,
    FreshTokenRequiredError,
    TokenRevokedError
)

from .api_exceptions import (
    BadRequestError,
    UnauthorizedError,
    ForbiddenError,
    MethodNotAllowedError,
    InternalServerError,
    ServiceUnavailableError,
    GatewayTimeoutError
)

from .llm_exceptions import (
    LLMError,
    LLMProviderError,
    LLMAuthenticationError,
    LLMQuotaError,
    LLMTimeoutError,
    LLMModelError,
    LLMServiceError
)

from .data_exceptions import (
    DatabaseError,
    DataValidationError,
    DataIntegrityError,
    MigrationError
)

__all__ = [
    # Base exceptions
    'AgentShopError',
    'APIError',
    'ValidationError',
    'AuthenticationError',
    'AuthorizationError',
    'NotFoundError',
    'ConflictError',
    'RateLimitError',
    'ServerError',
    'BusinessLogicError',
    'ExternalServiceError',
    
    # Auth exceptions
    'TokenExpiredError',
    'InvalidTokenError',
    'TokenRequiredError',
    'FreshTokenRequiredError',
    'TokenRevokedError',
    
    # API exceptions
    'BadRequestError',
    'UnauthorizedError',
    'ForbiddenError',
    'MethodNotAllowedError',
    'InternalServerError',
    'ServiceUnavailableError',
    'GatewayTimeoutError',
    
    # LLM exceptions
    'LLMError',
    'LLMProviderError',
    'LLMAuthenticationError',
    'LLMQuotaError',
    'LLMTimeoutError',
    'LLMModelError',
    'LLMServiceError',
    
    # Data exceptions
    'DatabaseError',
    'DataValidationError',
    'DataIntegrityError',
    'MigrationError'
]