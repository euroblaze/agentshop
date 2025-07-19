"""
Core API Module

Provides unified API patterns, controllers, and utilities for all AgentShop modules.
"""

from .pagination import (
    paginate_query,
    paginate_list,
    get_pagination_links,
    PaginationHelper,
    PaginationMeta
)

from .response_formatter import (
    ResponseFormatter,
    SuccessResponse,
    ErrorResponse,
    format_success,
    format_error,
    format_validation_error
)

__all__ = [
    # Pagination
    'paginate_query',
    'paginate_list', 
    'get_pagination_links',
    'PaginationHelper',
    'PaginationMeta',
    
    # Response formatting
    'ResponseFormatter',
    'SuccessResponse',
    'ErrorResponse',
    'format_success',
    'format_error',
    'format_validation_error'
]