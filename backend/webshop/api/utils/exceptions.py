#!/usr/bin/env python3
"""
API Exceptions - Custom exception classes for API operations
"""

from typing import Dict, Any, List, Optional


class APIError(Exception):
    """Base exception for API errors"""
    
    def __init__(self, message: str = "API Error", status_code: int = 400):
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class ValidationError(APIError):
    """Exception raised for validation errors"""
    
    def __init__(self, message: str = "Validation Error", errors: Dict[str, List[str]] = None):
        super().__init__(message, 400)
        self.errors = errors or {}


class AuthenticationError(APIError):
    """Exception raised for authentication failures"""
    
    def __init__(self, message: str = "Authentication Error"):
        super().__init__(message, 401)


class AuthorizationError(APIError):
    """Exception raised for authorization failures"""
    
    def __init__(self, message: str = "Authorization Error"):
        super().__init__(message, 403)


class NotFoundError(APIError):
    """Exception raised when resource is not found"""
    
    def __init__(self, message: str = "Resource Not Found"):
        super().__init__(message, 404)


class ConflictError(APIError):
    """Exception raised for resource conflicts"""
    
    def __init__(self, message: str = "Resource Conflict"):
        super().__init__(message, 409)


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded"""
    
    def __init__(self, message: str = "Rate Limit Exceeded"):
        super().__init__(message, 429)


class ServerError(APIError):
    """Exception raised for server errors"""
    
    def __init__(self, message: str = "Internal Server Error"):
        super().__init__(message, 500)