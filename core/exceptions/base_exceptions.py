#!/usr/bin/env python3
"""
Core Base Exceptions

Defines the foundational exception hierarchy for all AgentShop modules.
Provides comprehensive error handling with status codes, metadata, and context.
"""

from typing import Dict, Any, List, Optional, Union
import traceback
from datetime import datetime


class AgentShopError(Exception):
    """
    Base exception for all AgentShop errors.
    
    Provides a comprehensive foundation for error handling across
    all modules with support for error codes, metadata, and context.
    """
    
    def __init__(self, 
                 message: str = "An error occurred",
                 error_code: str = "GENERIC_ERROR",
                 status_code: int = 500,
                 details: Optional[Dict[str, Any]] = None,
                 original_error: Optional[Exception] = None,
                 context: Optional[Dict[str, Any]] = None):
        """
        Initialize AgentShop error.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code
            details: Additional error details
            original_error: Original exception that caused this error
            context: Additional context information
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.original_error = original_error
        self.context = context or {}
        self.timestamp = datetime.utcnow()
        self.traceback = traceback.format_exc() if original_error else None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary representation."""
        result = {
            'error_code': self.error_code,
            'message': self.message,
            'status_code': self.status_code,
            'timestamp': self.timestamp.isoformat(),
        }
        
        if self.details:
            result['details'] = self.details
        
        if self.context:
            result['context'] = self.context
        
        if self.original_error:
            result['original_error'] = str(self.original_error)
        
        return result
    
    def add_context(self, key: str, value: Any) -> 'AgentShopError':
        """Add context information to the error."""
        self.context[key] = value
        return self
    
    def add_detail(self, key: str, value: Any) -> 'AgentShopError':
        """Add detail information to the error."""
        self.details[key] = value
        return self
    
    def __str__(self) -> str:
        """String representation of the error."""
        return f"{self.error_code}: {self.message}"
    
    def __repr__(self) -> str:
        """Detailed string representation."""
        return (f"{self.__class__.__name__}("
                f"message='{self.message}', "
                f"error_code='{self.error_code}', "
                f"status_code={self.status_code})")


class APIError(AgentShopError):
    """Base exception for API-related errors."""
    
    def __init__(self, 
                 message: str = "API Error", 
                 error_code: str = "API_ERROR",
                 status_code: int = 400,
                 **kwargs):
        super().__init__(message, error_code, status_code, **kwargs)


class ValidationError(APIError):
    """Exception raised for validation errors."""
    
    def __init__(self, 
                 message: str = "Validation Error",
                 errors: Optional[Dict[str, List[str]]] = None,
                 field: Optional[str] = None,
                 **kwargs):
        """
        Initialize validation error.
        
        Args:
            message: Error message
            errors: Dictionary of field validation errors
            field: Specific field that failed validation
            **kwargs: Additional arguments
        """
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            **kwargs
        )
        self.errors = errors or {}
        self.field = field
        
        if field and field not in self.errors:
            self.errors[field] = [message]
        
        self.details.update({
            'validation_errors': self.errors,
            'failed_field': field
        })
    
    def add_field_error(self, field: str, error: str) -> 'ValidationError':
        """Add a field-specific validation error."""
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(error)
        self.details['validation_errors'] = self.errors
        return self
    
    def has_field_errors(self) -> bool:
        """Check if there are any field-specific errors."""
        return bool(self.errors)
    
    def get_field_errors(self, field: str) -> List[str]:
        """Get errors for a specific field."""
        return self.errors.get(field, [])


class AuthenticationError(APIError):
    """Exception raised for authentication failures."""
    
    def __init__(self, 
                 message: str = "Authentication Required",
                 auth_type: str = "bearer",
                 realm: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            status_code=401,
            **kwargs
        )
        self.auth_type = auth_type
        self.realm = realm
        
        self.details.update({
            'auth_type': auth_type,
            'realm': realm
        })


class AuthorizationError(APIError):
    """Exception raised for authorization failures."""
    
    def __init__(self, 
                 message: str = "Access Forbidden",
                 required_permission: Optional[str] = None,
                 required_role: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            status_code=403,
            **kwargs
        )
        self.required_permission = required_permission
        self.required_role = required_role
        
        self.details.update({
            'required_permission': required_permission,
            'required_role': required_role
        })


class NotFoundError(APIError):
    """Exception raised when resource is not found."""
    
    def __init__(self, 
                 message: str = "Resource Not Found",
                 resource_type: Optional[str] = None,
                 resource_id: Optional[Union[str, int]] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="NOT_FOUND_ERROR",
            status_code=404,
            **kwargs
        )
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        self.details.update({
            'resource_type': resource_type,
            'resource_id': resource_id
        })


class ConflictError(APIError):
    """Exception raised for resource conflicts."""
    
    def __init__(self, 
                 message: str = "Resource Conflict",
                 conflict_type: Optional[str] = None,
                 conflicting_field: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="CONFLICT_ERROR",
            status_code=409,
            **kwargs
        )
        self.conflict_type = conflict_type
        self.conflicting_field = conflicting_field
        
        self.details.update({
            'conflict_type': conflict_type,
            'conflicting_field': conflicting_field
        })


class RateLimitError(APIError):
    """Exception raised when rate limit is exceeded."""
    
    def __init__(self, 
                 message: str = "Rate Limit Exceeded",
                 limit: Optional[int] = None,
                 window: Optional[int] = None,
                 retry_after: Optional[int] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            **kwargs
        )
        self.limit = limit
        self.window = window
        self.retry_after = retry_after
        
        self.details.update({
            'limit': limit,
            'window': window,
            'retry_after': retry_after
        })


class ServerError(AgentShopError):
    """Exception raised for server errors."""
    
    def __init__(self, 
                 message: str = "Internal Server Error",
                 error_code: str = "SERVER_ERROR",
                 **kwargs):
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=500,
            **kwargs
        )


class BusinessLogicError(AgentShopError):
    """Exception raised for business logic violations."""
    
    def __init__(self, 
                 message: str = "Business Logic Error",
                 rule: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            status_code=422,
            **kwargs
        )
        self.rule = rule
        
        if rule:
            self.details['violated_rule'] = rule


class ExternalServiceError(AgentShopError):
    """Exception raised for external service failures."""
    
    def __init__(self, 
                 message: str = "External Service Error",
                 service_name: Optional[str] = None,
                 service_error_code: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            **kwargs
        )
        self.service_name = service_name
        self.service_error_code = service_error_code
        
        self.details.update({
            'service_name': service_name,
            'service_error_code': service_error_code
        })


# Utility functions for error handling

def create_validation_error(field_errors: Dict[str, List[str]], 
                          message: str = "Validation failed") -> ValidationError:
    """
    Create a validation error from field errors.
    
    Args:
        field_errors: Dictionary of field validation errors
        message: Overall error message
        
    Returns:
        ValidationError instance
    """
    error = ValidationError(message)
    error.errors = field_errors
    error.details['validation_errors'] = field_errors
    return error


def wrap_external_error(external_error: Exception, 
                       service_name: str,
                       context: Optional[Dict[str, Any]] = None) -> ExternalServiceError:
    """
    Wrap an external service error in our exception hierarchy.
    
    Args:
        external_error: Original external error
        service_name: Name of the external service
        context: Additional context
        
    Returns:
        ExternalServiceError instance
    """
    return ExternalServiceError(
        message=f"Error from {service_name}: {str(external_error)}",
        service_name=service_name,
        original_error=external_error,
        context=context
    )


def is_client_error(error: AgentShopError) -> bool:
    """Check if error is a client error (4xx status code)."""
    return 400 <= error.status_code < 500


def is_server_error(error: AgentShopError) -> bool:
    """Check if error is a server error (5xx status code)."""
    return 500 <= error.status_code < 600


def get_error_category(error: AgentShopError) -> str:
    """Get the category of an error based on status code."""
    if is_client_error(error):
        return "client_error"
    elif is_server_error(error):
        return "server_error"
    else:
        return "unknown"