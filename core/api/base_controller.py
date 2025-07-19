#!/usr/bin/env python3
"""
Core Base Controller

Provides unified controller functionality for all AgentShop API modules.
Enhanced from the webshop base controller with additional features and framework flexibility.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Union, Type
from abc import ABC, abstractmethod
from functools import wraps
from datetime import datetime

# Core imports
from ..exceptions import (
    AgentShopError, APIError, ValidationError, AuthenticationError, 
    AuthorizationError, NotFoundError, RateLimitError
)
from ..validation import validate_request_data, JSONSchemaValidator
from .pagination import PaginationHelper, extract_pagination_params
from .response_formatter import ResponseFormatter

logger = logging.getLogger(__name__)


class BaseController(ABC):
    """
    Abstract base controller providing comprehensive API functionality.
    
    Features:
    - Standardized response formatting
    - Request validation and parsing
    - Pagination support
    - Error handling
    - Authentication decorators
    - Framework-agnostic design
    """
    
    def __init__(self, response_formatter: Optional[ResponseFormatter] = None):
        """
        Initialize base controller.
        
        Args:
            response_formatter: Custom response formatter instance
        """
        self.response_formatter = response_formatter or ResponseFormatter()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    # Response Methods
    
    def success_response(self, 
                        data: Any = None, 
                        message: str = "Operation completed successfully",
                        meta: Optional[Dict[str, Any]] = None,
                        status_code: int = 200) -> Tuple[Dict[str, Any], int]:
        """
        Create standardized success response.
        
        Args:
            data: Response data
            message: Success message
            meta: Additional metadata
            status_code: HTTP status code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return self.response_formatter.success(data, message, meta, status_code)
    
    def error_response(self, 
                      message: str,
                      error_code: str = "ERROR",
                      details: Optional[Dict[str, Any]] = None,
                      status_code: int = 400) -> Tuple[Dict[str, Any], int]:
        """
        Create standardized error response.
        
        Args:
            message: Error message
            error_code: Machine-readable error code
            details: Additional error details
            status_code: HTTP status code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return self.response_formatter.error(message, error_code, details, status_code)
    
    def validation_error_response(self, 
                                 field_errors: Dict[str, List[str]],
                                 message: str = "Validation failed") -> Tuple[Dict[str, Any], int]:
        """
        Create validation error response.
        
        Args:
            field_errors: Dictionary of field validation errors
            message: Overall validation message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return self.response_formatter.validation_error(field_errors, message)
    
    def paginated_response(self, 
                          items: List[Any],
                          pagination_helper: PaginationHelper,
                          total: int,
                          message: str = "Data retrieved successfully") -> Tuple[Dict[str, Any], int]:
        """
        Create paginated response.
        
        Args:
            items: List of items for current page
            pagination_helper: Pagination helper instance
            total: Total number of items
            message: Success message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        pagination_meta = pagination_helper.create_meta(total)
        return self.response_formatter.paginated_success(items, pagination_meta.to_dict(), message)
    
    def created_response(self, 
                        data: Any = None,
                        message: str = "Resource created successfully",
                        location: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """
        Create resource creation response.
        
        Args:
            data: Created resource data
            message: Creation message
            location: URL of created resource
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return self.response_formatter.created(data, message, location)
    
    def not_found_response(self, 
                          message: str = "Resource not found",
                          resource_type: Optional[str] = None,
                          resource_id: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """
        Create not found response.
        
        Args:
            message: Not found message
            resource_type: Type of resource
            resource_id: ID of resource
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return self.response_formatter.not_found(message, resource_type, resource_id)
    
    # Request Parsing Methods
    
    @abstractmethod
    def get_request_json(self) -> Dict[str, Any]:
        """Get JSON data from request. Must be implemented by framework-specific controllers."""
        pass
    
    @abstractmethod
    def get_request_args(self) -> Dict[str, Any]:
        """Get query parameters from request. Must be implemented by framework-specific controllers."""
        pass
    
    @abstractmethod
    def is_json_request(self) -> bool:
        """Check if request contains JSON data. Must be implemented by framework-specific controllers."""
        pass
    
    def validate_json_request(self, 
                             schema: Optional[Dict[str, Any]] = None,
                             required_fields: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Validate JSON request data.
        
        Args:
            schema: JSON schema for validation
            required_fields: List of required field names
            
        Returns:
            Validated request data
            
        Raises:
            ValidationError: If validation fails
        """
        if not self.is_json_request():
            raise ValidationError("Request must contain JSON data")
        
        data = self.get_request_json()
        if not data:
            raise ValidationError("Request body cannot be empty")
        
        # Validate required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                field_errors = {field: [f"{field} is required"] for field in missing_fields}
                raise ValidationError("Missing required fields", field_errors)
        
        # Schema validation
        if schema:
            validation_errors = validate_request_data(data, schema)
            if validation_errors:
                raise ValidationError("Validation failed", validation_errors)
        
        return data
    
    def get_pagination_params(self, 
                             default_per_page: int = 20,
                             max_per_page: int = 100) -> PaginationHelper:
        """
        Extract pagination parameters from request.
        
        Args:
            default_per_page: Default items per page
            max_per_page: Maximum allowed items per page
            
        Returns:
            PaginationHelper instance
        """
        request_args = self.get_request_args()
        page, per_page = extract_pagination_params(request_args, default_per_page, max_per_page)
        return PaginationHelper(page, per_page, max_per_page, default_per_page)
    
    def get_search_params(self) -> Dict[str, Any]:
        """
        Extract search parameters from request.
        
        Returns:
            Dictionary with search parameters
        """
        request_args = self.get_request_args()
        
        return {
            'search': request_args.get('search', '').strip(),
            'sort_by': request_args.get('sort_by', 'id'),
            'sort_order': request_args.get('sort_order', 'desc').lower(),
            'filters': self._extract_filters(request_args)
        }
    
    def _extract_filters(self, request_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract filter parameters from request arguments.
        
        Args:
            request_args: Request arguments dictionary
            
        Returns:
            Dictionary of filter parameters
        """
        filters = {}
        
        # Common filter parameters
        filter_params = [
            'status', 'category', 'type', 'active', 'verified', 
            'published', 'featured', 'archived', 'deleted'
        ]
        
        for param in filter_params:
            value = request_args.get(param)
            if value is not None:
                # Handle boolean string values
                if value.lower() in ('true', 'false'):
                    filters[param] = value.lower() == 'true'
                else:
                    filters[param] = value
        
        # Handle date range filters
        date_filters = ['created_after', 'created_before', 'updated_after', 'updated_before']
        for date_filter in date_filters:
            value = request_args.get(date_filter)
            if value:
                try:
                    # Try to parse ISO format date
                    filters[date_filter] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    # Skip invalid date formats
                    continue
        
        return filters
    
    # Error Handling
    
    def handle_exception(self, exception: Exception) -> Tuple[Dict[str, Any], int]:
        """
        Handle exceptions and convert to API responses.
        
        Args:
            exception: Exception to handle
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        if isinstance(exception, ValidationError):
            self.logger.warning(f"Validation error: {exception}")
            return self.validation_error_response(exception.errors, str(exception))
        
        elif isinstance(exception, AuthenticationError):
            self.logger.warning(f"Authentication error: {exception}")
            return self.error_response(
                str(exception), 
                "AUTHENTICATION_ERROR", 
                status_code=401
            )
        
        elif isinstance(exception, AuthorizationError):
            self.logger.warning(f"Authorization error: {exception}")
            return self.error_response(
                str(exception),
                "AUTHORIZATION_ERROR",
                status_code=403
            )
        
        elif isinstance(exception, NotFoundError):
            self.logger.info(f"Not found error: {exception}")
            return self.not_found_response(str(exception))
        
        elif isinstance(exception, RateLimitError):
            self.logger.warning(f"Rate limit error: {exception}")
            return self.error_response(
                str(exception),
                "RATE_LIMIT_ERROR",
                status_code=429
            )
        
        elif isinstance(exception, AgentShopError):
            self.logger.error(f"AgentShop error: {exception}")
            return self.error_response(
                exception.message,
                exception.error_code,
                exception.details,
                exception.status_code
            )
        
        else:
            # Generic exception handling
            self.logger.error(f"Unexpected error: {exception}", exc_info=True)
            return self.error_response(
                "Internal server error",
                "INTERNAL_SERVER_ERROR",
                status_code=500
            )
    
    # Utility Methods
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID from authentication context. Override in framework-specific controllers."""
        return None
    
    def get_current_user_claims(self) -> Optional[Dict[str, Any]]:
        """Get current user claims from authentication context. Override in framework-specific controllers."""
        return None
    
    def is_admin_user(self) -> bool:
        """Check if current user is admin. Override in framework-specific controllers."""
        claims = self.get_current_user_claims()
        return claims.get('is_admin', False) if claims else False


class FlaskController(BaseController):
    """Flask-specific implementation of BaseController."""
    
    def get_request_json(self) -> Dict[str, Any]:
        """Get JSON data from Flask request."""
        from flask import request
        return request.get_json() or {}
    
    def get_request_args(self) -> Dict[str, Any]:
        """Get query parameters from Flask request."""
        from flask import request
        return request.args.to_dict()
    
    def is_json_request(self) -> bool:
        """Check if Flask request contains JSON data."""
        from flask import request
        return request.is_json
    
    def get_current_user_id(self) -> Optional[str]:
        """Get current user ID from Flask-JWT-Extended."""
        try:
            from flask_jwt_extended import get_jwt_identity
            return get_jwt_identity()
        except ImportError:
            return None
    
    def get_current_user_claims(self) -> Optional[Dict[str, Any]]:
        """Get current user claims from Flask-JWT-Extended."""
        try:
            from flask_jwt_extended import get_jwt
            return get_jwt()
        except ImportError:
            return None


# Decorators for authentication and authorization

def require_auth(framework: str = 'flask'):
    """
    Decorator to require authentication.
    
    Args:
        framework: Framework type ('flask', 'fastapi', 'django')
        
    Usage:
        @require_auth()
        def protected_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if framework == 'flask':
                try:
                    from flask_jwt_extended import verify_jwt_in_request
                    verify_jwt_in_request()
                    return f(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Authentication failed: {e}")
                    raise AuthenticationError("Authentication required")
            
            elif framework == 'fastapi':
                # FastAPI authentication would be handled via dependencies
                return f(*args, **kwargs)
            
            elif framework == 'django':
                # Django authentication would be handled via middleware
                return f(*args, **kwargs)
            
            else:
                # Generic authentication check
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def require_admin(framework: str = 'flask'):
    """
    Decorator to require admin privileges.
    
    Args:
        framework: Framework type ('flask', 'fastapi', 'django')
        
    Usage:
        @require_admin()
        def admin_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if framework == 'flask':
                try:
                    from flask_jwt_extended import verify_jwt_in_request, get_jwt
                    verify_jwt_in_request()
                    claims = get_jwt()
                    if not claims.get('is_admin', False):
                        raise AuthorizationError("Admin privileges required")
                    return f(*args, **kwargs)
                except AuthorizationError:
                    raise
                except Exception as e:
                    logger.warning(f"Admin authentication failed: {e}")
                    raise AuthenticationError("Authentication required")
            
            else:
                # Other frameworks would implement their own admin checks
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def handle_api_errors(controller_class: Type[BaseController] = None):
    """
    Decorator to handle API errors automatically.
    
    Args:
        controller_class: Controller class to use for error handling
        
    Usage:
        @handle_api_errors()
        def api_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # Use controller instance if available, otherwise create a basic one
                if args and isinstance(args[0], BaseController):
                    controller = args[0]
                elif controller_class:
                    controller = controller_class()
                else:
                    controller = FlaskController()  # Default to Flask
                
                return controller.handle_exception(e)
        
        return decorated_function
    return decorator


def rate_limit(limit: str, framework: str = 'flask'):
    """
    Decorator for rate limiting endpoints.
    
    Args:
        limit: Rate limit string (e.g., "100/hour", "10/minute")
        framework: Framework type for rate limiting implementation
        
    Usage:
        @rate_limit("100/hour")
        def api_endpoint():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if framework == 'flask':
                # Flask rate limiting would be handled by flask-limiter
                # This decorator just marks the endpoint for configuration
                pass
            elif framework == 'fastapi':
                # FastAPI rate limiting would be handled by slowapi or similar
                pass
            elif framework == 'django':
                # Django rate limiting would be handled by django-ratelimit
                pass
            
            return f(*args, **kwargs)
        
        decorated_function._rate_limit = limit
        decorated_function._rate_limit_framework = framework
        return decorated_function
    
    return decorator


def validate_schema(schema: Dict[str, Any], required_fields: Optional[List[str]] = None):
    """
    Decorator to validate request data against a schema.
    
    Args:
        schema: JSON schema for validation
        required_fields: List of required field names
        
    Usage:
        @validate_schema(USER_SCHEMA, ['name', 'email'])
        def create_user():
            pass
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get controller instance
            if args and isinstance(args[0], BaseController):
                controller = args[0]
                validated_data = controller.validate_json_request(schema, required_fields)
                # Add validated data to kwargs
                kwargs['validated_data'] = validated_data
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


# Factory function for creating framework-specific controllers

def create_controller(framework: str = 'flask', **kwargs) -> BaseController:
    """
    Factory function to create framework-specific controller instances.
    
    Args:
        framework: Framework type ('flask', 'fastapi', 'django')
        **kwargs: Additional arguments for controller initialization
        
    Returns:
        Framework-specific controller instance
    """
    if framework.lower() == 'flask':
        return FlaskController(**kwargs)
    
    elif framework.lower() == 'fastapi':
        # FastAPI controller would be implemented when needed
        class FastAPIController(BaseController):
            def get_request_json(self): return {}
            def get_request_args(self): return {}
            def is_json_request(self): return True
        return FastAPIController(**kwargs)
    
    elif framework.lower() == 'django':
        # Django controller would be implemented when needed
        class DjangoController(BaseController):
            def get_request_json(self): return {}
            def get_request_args(self): return {}
            def is_json_request(self): return True
        return DjangoController(**kwargs)
    
    else:
        raise ValueError(f"Unsupported framework: {framework}")


# Default controller instance for convenience
default_controller = FlaskController()