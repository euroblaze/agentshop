#!/usr/bin/env python3
"""
API Response Formatting

Provides standardized response formatting for all AgentShop API endpoints.
Ensures consistent response structure across all modules.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
from dataclasses import dataclass, asdict
import json

from ..exceptions import AgentShopError, ValidationError


@dataclass
class SuccessResponse:
    """Standardized success response structure."""
    
    success: bool = True
    data: Any = None
    message: str = "Operation completed successfully"
    meta: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        # Remove None values for cleaner response
        return {k: v for k, v in result.items() if v is not None}


@dataclass 
class ErrorResponse:
    """Standardized error response structure."""
    
    success: bool = False
    error_code: str = "ERROR"
    message: str = "An error occurred"
    details: Optional[Dict[str, Any]] = None
    timestamp: Optional[str] = None
    request_id: Optional[str] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        result = asdict(self)
        # Remove None values for cleaner response
        return {k: v for k, v in result.items() if v is not None}


class ResponseFormatter:
    """
    Comprehensive response formatter for API endpoints.
    
    Provides methods to format various types of responses with
    consistent structure and metadata.
    """
    
    def __init__(self, 
                 include_timestamp: bool = True,
                 include_request_id: bool = False,
                 default_success_message: str = "Operation completed successfully"):
        """
        Initialize response formatter.
        
        Args:
            include_timestamp: Whether to include timestamp in responses
            include_request_id: Whether to include request ID in responses
            default_success_message: Default message for success responses
        """
        self.include_timestamp = include_timestamp
        self.include_request_id = include_request_id
        self.default_success_message = default_success_message
    
    def success(self, 
                data: Any = None, 
                message: Optional[str] = None,
                meta: Optional[Dict[str, Any]] = None,
                status_code: int = 200) -> Tuple[Dict[str, Any], int]:
        """
        Format success response.
        
        Args:
            data: Response data
            message: Success message
            meta: Additional metadata
            status_code: HTTP status code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = SuccessResponse(
            data=data,
            message=message or self.default_success_message,
            meta=meta,
            timestamp=datetime.utcnow().isoformat() if self.include_timestamp else None
        )
        
        return response.to_dict(), status_code
    
    def error(self,
              message: str,
              error_code: str = "ERROR",
              details: Optional[Dict[str, Any]] = None,
              status_code: int = 400,
              request_id: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """
        Format error response.
        
        Args:
            message: Error message
            error_code: Machine-readable error code
            details: Additional error details
            status_code: HTTP status code
            request_id: Request ID for tracking
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        response = ErrorResponse(
            error_code=error_code,
            message=message,
            details=details,
            timestamp=datetime.utcnow().isoformat() if self.include_timestamp else None,
            request_id=request_id if self.include_request_id else None
        )
        
        return response.to_dict(), status_code
    
    def validation_error(self,
                        field_errors: Dict[str, List[str]],
                        message: str = "Validation failed",
                        status_code: int = 400) -> Tuple[Dict[str, Any], int]:
        """
        Format validation error response.
        
        Args:
            field_errors: Dictionary of field validation errors
            message: Overall validation message
            status_code: HTTP status code
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        details = {
            'validation_errors': field_errors,
            'total_errors': sum(len(errors) for errors in field_errors.values())
        }
        
        return self.error(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=status_code
        )
    
    def paginated_success(self,
                         items: List[Any],
                         pagination_meta: Dict[str, Any],
                         message: Optional[str] = None,
                         additional_meta: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], int]:
        """
        Format paginated success response.
        
        Args:
            items: List of items for current page
            pagination_meta: Pagination metadata
            message: Success message
            additional_meta: Additional metadata
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        meta = {'pagination': pagination_meta}
        if additional_meta:
            meta.update(additional_meta)
        
        return self.success(
            data=items,
            message=message,
            meta=meta,
            status_code=200
        )
    
    def created(self,
                data: Any = None,
                message: str = "Resource created successfully",
                location: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """
        Format resource creation response.
        
        Args:
            data: Created resource data
            message: Creation message
            location: URL of created resource
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        meta = {'location': location} if location else None
        
        return self.success(
            data=data,
            message=message,
            meta=meta,
            status_code=201
        )
    
    def updated(self,
                data: Any = None,
                message: str = "Resource updated successfully") -> Tuple[Dict[str, Any], int]:
        """
        Format resource update response.
        
        Args:
            data: Updated resource data
            message: Update message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return self.success(
            data=data,
            message=message,
            status_code=200
        )
    
    def deleted(self,
                message: str = "Resource deleted successfully") -> Tuple[Dict[str, Any], int]:
        """
        Format resource deletion response.
        
        Args:
            message: Deletion message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return self.success(
            data=None,
            message=message,
            status_code=200
        )
    
    def not_found(self,
                  message: str = "Resource not found",
                  resource_type: Optional[str] = None,
                  resource_id: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """
        Format not found error response.
        
        Args:
            message: Not found message
            resource_type: Type of resource not found
            resource_id: ID of resource not found
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        details = {}
        if resource_type:
            details['resource_type'] = resource_type
        if resource_id:
            details['resource_id'] = resource_id
        
        return self.error(
            message=message,
            error_code="NOT_FOUND",
            details=details if details else None,
            status_code=404
        )
    
    def unauthorized(self,
                    message: str = "Authentication required") -> Tuple[Dict[str, Any], int]:
        """
        Format unauthorized error response.
        
        Args:
            message: Unauthorized message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return self.error(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401
        )
    
    def forbidden(self,
                  message: str = "Access forbidden") -> Tuple[Dict[str, Any], int]:
        """
        Format forbidden error response.
        
        Args:
            message: Forbidden message
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        return self.error(
            message=message,
            error_code="FORBIDDEN",
            status_code=403
        )
    
    def rate_limited(self,
                    message: str = "Rate limit exceeded",
                    retry_after: Optional[int] = None) -> Tuple[Dict[str, Any], int]:
        """
        Format rate limit error response.
        
        Args:
            message: Rate limit message
            retry_after: Seconds to wait before retry
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        details = {'retry_after': retry_after} if retry_after else None
        
        return self.error(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            status_code=429
        )
    
    def internal_error(self,
                      message: str = "Internal server error",
                      error_id: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """
        Format internal server error response.
        
        Args:
            message: Error message
            error_id: Error tracking ID
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        details = {'error_id': error_id} if error_id else None
        
        return self.error(
            message=message,
            error_code="INTERNAL_SERVER_ERROR",
            details=details,
            status_code=500
        )
    
    def from_exception(self, 
                      exception: Exception,
                      request_id: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
        """
        Format response from an exception.
        
        Args:
            exception: Exception to format
            request_id: Request ID for tracking
            
        Returns:
            Tuple of (response_dict, status_code)
        """
        if isinstance(exception, AgentShopError):
            return self.error(
                message=exception.message,
                error_code=exception.error_code,
                details=exception.details if exception.details else None,
                status_code=exception.status_code,
                request_id=request_id
            )
        elif isinstance(exception, ValidationError):
            return self.validation_error(
                field_errors=exception.errors,
                message=exception.message
            )
        else:
            # Generic exception handling
            return self.internal_error(
                message=str(exception),
                error_id=request_id
            )


# Global response formatter instance
response_formatter = ResponseFormatter()


# Convenience functions for common responses

def format_success(data: Any = None, 
                  message: Optional[str] = None,
                  meta: Optional[Dict[str, Any]] = None,
                  status_code: int = 200) -> Tuple[Dict[str, Any], int]:
    """Format success response using global formatter."""
    return response_formatter.success(data, message, meta, status_code)


def format_error(message: str,
                error_code: str = "ERROR",
                details: Optional[Dict[str, Any]] = None,
                status_code: int = 400) -> Tuple[Dict[str, Any], int]:
    """Format error response using global formatter."""
    return response_formatter.error(message, error_code, details, status_code)


def format_validation_error(field_errors: Dict[str, List[str]],
                           message: str = "Validation failed") -> Tuple[Dict[str, Any], int]:
    """Format validation error response using global formatter."""
    return response_formatter.validation_error(field_errors, message)


def format_paginated_response(items: List[Any],
                             pagination_meta: Dict[str, Any],
                             message: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
    """Format paginated response using global formatter."""
    return response_formatter.paginated_success(items, pagination_meta, message)


def format_created_response(data: Any = None,
                           message: str = "Resource created successfully",
                           location: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
    """Format resource creation response using global formatter."""
    return response_formatter.created(data, message, location)


def format_not_found_response(message: str = "Resource not found",
                             resource_type: Optional[str] = None,
                             resource_id: Optional[str] = None) -> Tuple[Dict[str, Any], int]:
    """Format not found response using global formatter."""
    return response_formatter.not_found(message, resource_type, resource_id)


# Response wrapper for Flask/FastAPI integration

class ResponseWrapper:
    """Wrapper for framework-specific response objects."""
    
    def __init__(self, framework: str = 'flask'):
        """
        Initialize response wrapper.
        
        Args:
            framework: Framework type ('flask', 'fastapi', 'django')
        """
        self.framework = framework.lower()
        self.formatter = ResponseFormatter()
    
    def wrap_response(self, 
                     response_data: Dict[str, Any], 
                     status_code: int,
                     headers: Optional[Dict[str, str]] = None):
        """
        Wrap response data in framework-specific response object.
        
        Args:
            response_data: Response data dictionary
            status_code: HTTP status code
            headers: Additional headers
            
        Returns:
            Framework-specific response object
        """
        if self.framework == 'flask':
            from flask import jsonify, make_response
            response = make_response(jsonify(response_data), status_code)
            if headers:
                for key, value in headers.items():
                    response.headers[key] = value
            return response
        
        elif self.framework == 'fastapi':
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content=response_data,
                status_code=status_code,
                headers=headers
            )
        
        elif self.framework == 'django':
            from django.http import JsonResponse
            response = JsonResponse(response_data, status=status_code)
            if headers:
                for key, value in headers.items():
                    response[key] = value
            return response
        
        else:
            # Return raw data if framework not supported
            return response_data, status_code


# Configuration for different response formats

RESPONSE_CONFIGS = {
    'default': {
        'include_timestamp': True,
        'include_request_id': False,
        'success_message': 'Operation completed successfully'
    },
    'minimal': {
        'include_timestamp': False,
        'include_request_id': False,
        'success_message': 'Success'
    },
    'verbose': {
        'include_timestamp': True,
        'include_request_id': True,
        'success_message': 'Operation completed successfully'
    }
}


def get_response_formatter(config_name: str = 'default') -> ResponseFormatter:
    """
    Get response formatter with specific configuration.
    
    Args:
        config_name: Name of the configuration
        
    Returns:
        Configured ResponseFormatter instance
    """
    config = RESPONSE_CONFIGS.get(config_name, RESPONSE_CONFIGS['default'])
    return ResponseFormatter(**config)