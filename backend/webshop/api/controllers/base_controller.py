#!/usr/bin/env python3
"""
Base Controller - Common functionality for all API controllers
Provides standardized response formats, validation, and error handling
"""

from flask import jsonify, request, g
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from functools import wraps
import logging
from typing import Dict, Any, List, Optional, Tuple

from ..utils.exceptions import APIError, ValidationError, AuthenticationError
from ..utils.validators import validate_request_data
from ..utils.pagination import paginate_query
from ...services.base_service import ServiceError

logger = logging.getLogger(__name__)


class BaseController:
    """Base controller providing common functionality"""
    
    @staticmethod
    def success_response(data: Any = None, message: str = "Success", 
                        status_code: int = 200, meta: Dict = None) -> Tuple[Dict, int]:
        """
        Create standardized success response
        
        Args:
            data: Response data
            message: Success message
            status_code: HTTP status code
            meta: Additional metadata
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            'success': True,
            'message': message,
            'data': data
        }
        
        if meta:
            response['meta'] = meta
            
        return response, status_code
    
    @staticmethod
    def error_response(message: str = "Error", status_code: int = 400,
                      errors: Dict = None, error_code: str = None) -> Tuple[Dict, int]:
        """
        Create standardized error response
        
        Args:
            message: Error message
            status_code: HTTP status code
            errors: Detailed error information
            error_code: Application-specific error code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = {
            'success': False,
            'message': message
        }
        
        if errors:
            response['errors'] = errors
        if error_code:
            response['error_code'] = error_code
            
        return response, status_code
    
    @staticmethod
    def paginated_response(items: List, total: int, page: int, 
                          per_page: int, message: str = "Success") -> Tuple[Dict, int]:
        """
        Create paginated response
        
        Args:
            items: List of items for current page
            total: Total number of items
            page: Current page number
            per_page: Items per page
            message: Success message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        import math
        
        meta = {
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'pages': math.ceil(total / per_page) if per_page > 0 else 0,
                'has_next': page * per_page < total,
                'has_prev': page > 1
            }
        }
        
        return BaseController.success_response(
            data=items, 
            message=message, 
            meta=meta
        )

    @staticmethod
    def validate_json_request(schema: Dict = None, required_fields: List[str] = None) -> Any:
        """
        Validate JSON request data
        
        Args:
            schema: JSON schema for validation
            required_fields: List of required field names
            
        Returns:
            Validated request data
            
        Raises:
            ValidationError: If validation fails
        """
        if not request.is_json:
            raise ValidationError("Request must be JSON")
        
        data = request.get_json()
        if not data:
            raise ValidationError("Request body cannot be empty")
        
        # Validate required fields
        if required_fields:
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
        
        # Schema validation (if provided)
        if schema:
            validation_errors = validate_request_data(data, schema)
            if validation_errors:
                raise ValidationError("Validation failed", validation_errors)
        
        return data

    @staticmethod
    def get_pagination_params() -> Tuple[int, int]:
        """
        Extract pagination parameters from request
        
        Returns:
            Tuple of (page, per_page)
        """
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 items per page
        
        if page < 1:
            page = 1
        if per_page < 1:
            per_page = 20
            
        return page, per_page

    @staticmethod
    def get_search_params() -> Dict[str, Any]:
        """
        Extract search parameters from request
        
        Returns:
            Dictionary with search parameters
        """
        return {
            'search': request.args.get('search', '').strip(),
            'sort_by': request.args.get('sort_by', 'id'),
            'sort_order': request.args.get('sort_order', 'desc'),
            'filters': BaseController._extract_filters()
        }

    @staticmethod  
    def _extract_filters() -> Dict[str, Any]:
        """Extract filter parameters from request"""
        filters = {}
        
        # Common filter parameters
        filter_params = ['status', 'category', 'type', 'active', 'verified']
        
        for param in filter_params:
            value = request.args.get(param)
            if value is not None:
                filters[param] = value
                
        return filters


def require_auth(f):
    """
    Decorator to require JWT authentication
    
    Usage:
        @require_auth
        def protected_endpoint():
            current_user_id = get_jwt_identity()
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            return f(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            raise AuthenticationError("Authentication required")
    
    return decorated_function


def require_admin(f):
    """
    Decorator to require admin authentication
    
    Usage:
        @require_admin
        def admin_endpoint():
            current_admin_id = get_jwt_identity()
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            verify_jwt_in_request()
            claims = get_jwt()
            if not claims.get('is_admin', False):
                raise AuthenticationError("Admin access required")
            return f(*args, **kwargs)
        except AuthenticationError:
            raise
        except Exception as e:
            logger.warning(f"Admin authentication failed: {e}")
            raise AuthenticationError("Authentication required")
    
    return decorated_function


def handle_service_errors(f):
    """
    Decorator to handle service layer errors and convert to API responses
    
    Usage:
        @handle_service_errors
        def endpoint():
            # Service layer calls that might raise ServiceError
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:
            logger.warning(f"Validation error: {e}")
            return BaseController.error_response(
                message=str(e),
                status_code=400,
                errors=getattr(e, 'errors', None)
            )
        except ServiceError as e:
            logger.error(f"Service error: {e}")
            return BaseController.error_response(
                message=str(e),
                status_code=400
            )
        except AuthenticationError as e:
            logger.warning(f"Authentication error: {e}")
            return BaseController.error_response(
                message=str(e),
                status_code=401
            )
        except APIError as e:
            logger.error(f"API error: {e}")
            return BaseController.error_response(
                message=str(e),
                status_code=getattr(e, 'status_code', 400)
            )
        except Exception as e:
            logger.error(f"Unexpected error in {f.__name__}: {e}", exc_info=True)
            return BaseController.error_response(
                message="Internal server error",
                status_code=500
            )
    
    return decorated_function


def rate_limit(limit: str):
    """
    Decorator for rate limiting endpoints
    
    Args:
        limit: Rate limit string (e.g., "100/hour", "10/minute")
        
    Usage:
        @rate_limit("100/hour")
        def api_endpoint():
            pass
    """
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Rate limiting is handled by flask-limiter
            # This decorator just marks the endpoint for configuration
            return f(*args, **kwargs)
        
        decorated_function._rate_limit = limit
        return decorated_function
    
    return decorator