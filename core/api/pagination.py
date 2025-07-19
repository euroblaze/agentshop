#!/usr/bin/env python3
"""
Core Pagination Utilities

Provides comprehensive pagination support for APIs and data queries.
Enhanced from the webshop pagination with additional features.
"""

import math
from typing import Tuple, Dict, Any, List, Optional, Union
from sqlalchemy.orm import Query
from dataclasses import dataclass, asdict


@dataclass
class PaginationMeta:
    """Pagination metadata information."""
    
    page: int
    per_page: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool
    next_page: Optional[int] = None
    prev_page: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class PaginationHelper:
    """
    Enhanced pagination helper with configurable options.
    
    Provides comprehensive pagination functionality for both
    SQLAlchemy queries and in-memory lists.
    """
    
    def __init__(self, 
                 page: int = 1, 
                 per_page: int = 20, 
                 max_per_page: int = 100,
                 default_per_page: int = 20):
        """
        Initialize pagination helper.
        
        Args:
            page: Page number (1-based)
            per_page: Items per page
            max_per_page: Maximum allowed items per page
            default_per_page: Default items per page if not specified
        """
        self.page = max(1, int(page)) if page else 1
        self.per_page = self._validate_per_page(per_page, max_per_page, default_per_page)
        self.max_per_page = max_per_page
        self.default_per_page = default_per_page
    
    def _validate_per_page(self, per_page: Optional[int], max_per_page: int, default_per_page: int) -> int:
        """Validate and normalize per_page value."""
        if per_page is None:
            return default_per_page
        
        try:
            per_page = int(per_page)
            return max(1, min(per_page, max_per_page))
        except (ValueError, TypeError):
            return default_per_page
    
    def get_offset(self) -> int:
        """Get offset for database queries."""
        return (self.page - 1) * self.per_page
    
    def get_limit(self) -> int:
        """Get limit for database queries."""
        return self.per_page
    
    def create_meta(self, total: int) -> PaginationMeta:
        """Create pagination metadata."""
        total_pages = math.ceil(total / self.per_page) if self.per_page > 0 else 0
        has_next = self.page < total_pages
        has_prev = self.page > 1
        
        return PaginationMeta(
            page=self.page,
            per_page=self.per_page,
            total=total,
            pages=total_pages,
            has_next=has_next,
            has_prev=has_prev,
            next_page=self.page + 1 if has_next else None,
            prev_page=self.page - 1 if has_prev else None
        )
    
    def paginate_query(self, query: Query) -> Tuple[List[Any], PaginationMeta]:
        """
        Paginate SQLAlchemy query.
        
        Args:
            query: SQLAlchemy query object
            
        Returns:
            Tuple of (items, pagination_meta)
        """
        # Get total count efficiently
        total = query.count()
        
        # Get items for current page
        items = query.offset(self.get_offset()).limit(self.get_limit()).all()
        
        # Create pagination metadata
        meta = self.create_meta(total)
        
        return items, meta
    
    def paginate_list(self, items: List[Any]) -> Tuple[List[Any], PaginationMeta]:
        """
        Paginate a list of items.
        
        Args:
            items: List of items to paginate
            
        Returns:
            Tuple of (page_items, pagination_meta)
        """
        total = len(items)
        
        # Calculate slice boundaries
        start = self.get_offset()
        end = start + self.per_page
        
        # Get items for current page
        page_items = items[start:end]
        
        # Create pagination metadata
        meta = self.create_meta(total)
        
        return page_items, meta
    
    def get_page_range(self, total_pages: int, window: int = 5) -> List[int]:
        """
        Get page numbers for pagination navigation.
        
        Args:
            total_pages: Total number of pages
            window: Number of pages to show around current page
            
        Returns:
            List of page numbers to display
        """
        if total_pages <= window:
            return list(range(1, total_pages + 1))
        
        half_window = window // 2
        
        if self.page <= half_window:
            return list(range(1, window + 1))
        elif self.page > total_pages - half_window:
            return list(range(total_pages - window + 1, total_pages + 1))
        else:
            return list(range(self.page - half_window, self.page + half_window + 1))
    
    def is_valid_page(self, total: int) -> bool:
        """Check if current page is valid for the given total."""
        if total == 0:
            return self.page == 1
        
        total_pages = math.ceil(total / self.per_page)
        return 1 <= self.page <= total_pages


def paginate_query(query: Query, page: int = 1, per_page: int = 20) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Paginate SQLAlchemy query (backward compatibility function).
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Tuple of (items, pagination_meta)
    """
    helper = PaginationHelper(page, per_page)
    items, meta = helper.paginate_query(query)
    return items, meta.to_dict()


def paginate_list(items: List[Any], page: int = 1, per_page: int = 20) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Paginate a list of items (backward compatibility function).
    
    Args:
        items: List of items to paginate
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Tuple of (page_items, pagination_meta)
    """
    helper = PaginationHelper(page, per_page)
    page_items, meta = helper.paginate_list(items)
    return page_items, meta.to_dict()


def get_pagination_links(base_url: str, 
                        pagination_meta: Union[PaginationMeta, Dict[str, Any]],
                        query_params: Optional[Dict[str, str]] = None) -> Dict[str, Optional[str]]:
    """
    Generate pagination links for API responses.
    
    Args:
        base_url: Base URL for the endpoint
        pagination_meta: Pagination metadata
        query_params: Additional query parameters
        
    Returns:
        Dictionary with pagination links
    """
    if isinstance(pagination_meta, dict):
        page = pagination_meta['page']
        per_page = pagination_meta['per_page']
        pages = pagination_meta['pages']
        has_next = pagination_meta['has_next']
        has_prev = pagination_meta['has_prev']
    else:
        page = pagination_meta.page
        per_page = pagination_meta.per_page
        pages = pagination_meta.pages
        has_next = pagination_meta.has_next
        has_prev = pagination_meta.has_prev
    
    if query_params is None:
        query_params = {}
    
    def build_url(page_num: int) -> str:
        """Build URL for specific page."""
        params = query_params.copy()
        params.update({'page': str(page_num), 'per_page': str(per_page)})
        query_string = '&'.join([f"{k}={v}" for k, v in params.items() if v is not None])
        return f"{base_url}?{query_string}" if query_string else base_url
    
    links = {
        'self': build_url(page),
        'first': build_url(1),
        'last': build_url(pages) if pages > 0 else build_url(1),
        'prev': build_url(page - 1) if has_prev else None,
        'next': build_url(page + 1) if has_next else None
    }
    
    return links


class CursorPagination:
    """
    Cursor-based pagination for large datasets.
    
    More efficient than offset-based pagination for large datasets
    as it doesn't suffer from the "offset problem".
    """
    
    def __init__(self, cursor_field: str = 'id', page_size: int = 20):
        """
        Initialize cursor pagination.
        
        Args:
            cursor_field: Field to use for cursor (must be ordered)
            page_size: Number of items per page
        """
        self.cursor_field = cursor_field
        self.page_size = page_size
    
    def paginate_query(self, 
                      query: Query, 
                      cursor: Optional[str] = None,
                      direction: str = 'next') -> Tuple[List[Any], Dict[str, Any]]:
        """
        Paginate query using cursor.
        
        Args:
            query: SQLAlchemy query
            cursor: Cursor value for pagination
            direction: 'next' or 'prev'
            
        Returns:
            Tuple of (items, cursor_meta)
        """
        # Get the cursor field from the model
        model = query.column_descriptions[0]['type']
        cursor_column = getattr(model, self.cursor_field)
        
        # Apply cursor filter
        if cursor:
            if direction == 'next':
                query = query.filter(cursor_column > cursor)
                query = query.order_by(cursor_column.asc())
            else:
                query = query.filter(cursor_column < cursor)
                query = query.order_by(cursor_column.desc())
        else:
            query = query.order_by(cursor_column.asc())
        
        # Get one extra item to check if there are more pages
        items = query.limit(self.page_size + 1).all()
        
        has_more = len(items) > self.page_size
        if has_more:
            items = items[:-1]  # Remove the extra item
        
        # Reverse items if we were going backwards
        if direction == 'prev' and cursor:
            items = list(reversed(items))
        
        # Generate cursors
        next_cursor = None
        prev_cursor = None
        
        if items:
            if direction == 'next' or not cursor:
                next_cursor = str(getattr(items[-1], self.cursor_field)) if has_more else None
                prev_cursor = str(getattr(items[0], self.cursor_field)) if cursor else None
            else:
                next_cursor = cursor
                prev_cursor = str(getattr(items[0], self.cursor_field)) if len(items) == self.page_size else None
        
        meta = {
            'page_size': self.page_size,
            'has_next': has_more if direction == 'next' else bool(next_cursor),
            'has_prev': bool(prev_cursor),
            'next_cursor': next_cursor,
            'prev_cursor': prev_cursor,
            'cursor_field': self.cursor_field
        }
        
        return items, meta


def create_pagination_response(items: List[Any], 
                              pagination_meta: Union[PaginationMeta, Dict[str, Any]],
                              base_url: Optional[str] = None,
                              query_params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Create a standardized pagination response.
    
    Args:
        items: List of items for current page
        pagination_meta: Pagination metadata
        base_url: Base URL for generating links
        query_params: Additional query parameters
        
    Returns:
        Standardized pagination response
    """
    response = {
        'data': items,
        'pagination': pagination_meta.to_dict() if isinstance(pagination_meta, PaginationMeta) else pagination_meta
    }
    
    if base_url:
        response['links'] = get_pagination_links(base_url, pagination_meta, query_params)
    
    return response


def extract_pagination_params(request_args: Dict[str, Any], 
                             default_per_page: int = 20,
                             max_per_page: int = 100) -> Tuple[int, int]:
    """
    Extract pagination parameters from request arguments.
    
    Args:
        request_args: Request arguments (e.g., from Flask request.args)
        default_per_page: Default items per page
        max_per_page: Maximum allowed items per page
        
    Returns:
        Tuple of (page, per_page)
    """
    try:
        page = max(1, int(request_args.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    
    try:
        per_page = int(request_args.get('per_page', default_per_page))
        per_page = max(1, min(per_page, max_per_page))
    except (ValueError, TypeError):
        per_page = default_per_page
    
    return page, per_page


# Configuration for different pagination styles

PAGINATION_CONFIGS = {
    'default': {
        'per_page': 20,
        'max_per_page': 100
    },
    'small': {
        'per_page': 10,
        'max_per_page': 50
    },
    'large': {
        'per_page': 50,
        'max_per_page': 200
    },
    'admin': {
        'per_page': 25,
        'max_per_page': 500
    }
}


def get_pagination_config(config_name: str = 'default') -> Dict[str, int]:
    """
    Get pagination configuration by name.
    
    Args:
        config_name: Name of the configuration
        
    Returns:
        Pagination configuration dictionary
    """
    return PAGINATION_CONFIGS.get(config_name, PAGINATION_CONFIGS['default'])