#!/usr/bin/env python3
"""
Pagination utilities for API responses
"""

from typing import Tuple, Dict, Any, List
from sqlalchemy.orm import Query
import math


def paginate_query(query: Query, page: int = 1, per_page: int = 20) -> Tuple[List, Dict[str, Any]]:
    """
    Paginate SQLAlchemy query
    
    Args:
        query: SQLAlchemy query object
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Tuple of (items, pagination_meta)
    """
    # Ensure positive values
    page = max(1, page)
    per_page = max(1, min(per_page, 100))  # Max 100 items per page
    
    # Get total count
    total = query.count()
    
    # Calculate pagination values
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    offset = (page - 1) * per_page
    
    # Get items for current page
    items = query.offset(offset).limit(per_page).all()
    
    # Create pagination metadata
    pagination_meta = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'next_page': page + 1 if page < total_pages else None,
        'prev_page': page - 1 if page > 1 else None
    }
    
    return items, pagination_meta


def paginate_list(items: List, page: int = 1, per_page: int = 20) -> Tuple[List, Dict[str, Any]]:
    """
    Paginate a list of items
    
    Args:
        items: List of items to paginate
        page: Page number (1-based)
        per_page: Items per page
        
    Returns:
        Tuple of (page_items, pagination_meta)
    """
    # Ensure positive values
    page = max(1, page)
    per_page = max(1, min(per_page, 100))  # Max 100 items per page
    
    total = len(items)
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0
    
    # Calculate slice boundaries
    start = (page - 1) * per_page
    end = start + per_page
    
    # Get items for current page
    page_items = items[start:end]
    
    # Create pagination metadata
    pagination_meta = {
        'page': page,
        'per_page': per_page,
        'total': total,
        'pages': total_pages,
        'has_next': page < total_pages,
        'has_prev': page > 1,
        'next_page': page + 1 if page < total_pages else None,
        'prev_page': page - 1 if page > 1 else None
    }
    
    return page_items, pagination_meta


def get_pagination_links(base_url: str, page: int, per_page: int, total_pages: int,
                        query_params: Dict[str, str] = None) -> Dict[str, str]:
    """
    Generate pagination links for API responses
    
    Args:
        base_url: Base URL for the endpoint
        page: Current page number
        per_page: Items per page
        total_pages: Total number of pages
        query_params: Additional query parameters
        
    Returns:
        Dictionary with pagination links
    """
    if query_params is None:
        query_params = {}
    
    def build_url(page_num: int) -> str:
        params = query_params.copy()
        params.update({'page': str(page_num), 'per_page': str(per_page)})
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        return f"{base_url}?{query_string}"
    
    links = {
        'self': build_url(page),
        'first': build_url(1),
        'last': build_url(total_pages) if total_pages > 0 else build_url(1)
    }
    
    if page > 1:
        links['prev'] = build_url(page - 1)
    
    if page < total_pages:
        links['next'] = build_url(page + 1)
    
    return links


class PaginationHelper:
    """Helper class for handling pagination logic"""
    
    def __init__(self, page: int = 1, per_page: int = 20, max_per_page: int = 100):
        """
        Initialize pagination helper
        
        Args:
            page: Page number (1-based)
            per_page: Items per page
            max_per_page: Maximum allowed items per page
        """
        self.page = max(1, page)
        self.per_page = max(1, min(per_page, max_per_page))
        self.max_per_page = max_per_page
    
    def get_offset(self) -> int:
        """Get offset for database queries"""
        return (self.page - 1) * self.per_page
    
    def get_limit(self) -> int:
        """Get limit for database queries"""
        return self.per_page
    
    def paginate_query(self, query: Query) -> Tuple[List, Dict[str, Any]]:
        """Paginate SQLAlchemy query"""
        return paginate_query(query, self.page, self.per_page)
    
    def paginate_list(self, items: List) -> Tuple[List, Dict[str, Any]]:
        """Paginate list of items"""
        return paginate_list(items, self.page, self.per_page)
    
    def get_page_info(self, total: int) -> Dict[str, Any]:
        """Get pagination information"""
        total_pages = math.ceil(total / self.per_page) if self.per_page > 0 else 0
        
        return {
            'page': self.page,
            'per_page': self.per_page,
            'total': total,
            'pages': total_pages,
            'has_next': self.page < total_pages,
            'has_prev': self.page > 1,
            'next_page': self.page + 1 if self.page < total_pages else None,
            'prev_page': self.page - 1 if self.page > 1 else None
        }