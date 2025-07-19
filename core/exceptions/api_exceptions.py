#!/usr/bin/env python3
"""
API-specific Exceptions

HTTP status code specific exceptions for API operations.
"""

from typing import Optional, Dict, Any
from .base_exceptions import APIError, ServerError


class BadRequestError(APIError):
    """Exception for 400 Bad Request errors."""
    
    def __init__(self, 
                 message: str = "Bad Request",
                 request_data: Optional[Dict[str, Any]] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="BAD_REQUEST",
            status_code=400,
            **kwargs
        )
        self.request_data = request_data
        
        if request_data:
            self.details['request_data'] = request_data


class UnauthorizedError(APIError):
    """Exception for 401 Unauthorized errors."""
    
    def __init__(self, 
                 message: str = "Unauthorized",
                 **kwargs):
        super().__init__(
            message=message,
            error_code="UNAUTHORIZED",
            status_code=401,
            **kwargs
        )


class ForbiddenError(APIError):
    """Exception for 403 Forbidden errors."""
    
    def __init__(self, 
                 message: str = "Forbidden",
                 **kwargs):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=403,
            **kwargs
        )


class MethodNotAllowedError(APIError):
    """Exception for 405 Method Not Allowed errors."""
    
    def __init__(self, 
                 message: str = "Method Not Allowed",
                 allowed_methods: Optional[list] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="METHOD_NOT_ALLOWED",
            status_code=405,
            **kwargs
        )
        self.allowed_methods = allowed_methods or []
        
        if self.allowed_methods:
            self.details['allowed_methods'] = self.allowed_methods


class NotAcceptableError(APIError):
    """Exception for 406 Not Acceptable errors."""
    
    def __init__(self, 
                 message: str = "Not Acceptable",
                 supported_types: Optional[list] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="NOT_ACCEPTABLE",
            status_code=406,
            **kwargs
        )
        self.supported_types = supported_types or []
        
        if self.supported_types:
            self.details['supported_types'] = self.supported_types


class RequestTimeoutError(APIError):
    """Exception for 408 Request Timeout errors."""
    
    def __init__(self, 
                 message: str = "Request Timeout",
                 timeout_duration: Optional[int] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="REQUEST_TIMEOUT",
            status_code=408,
            **kwargs
        )
        self.timeout_duration = timeout_duration
        
        if timeout_duration:
            self.details['timeout_duration'] = timeout_duration


class UnprocessableEntityError(APIError):
    """Exception for 422 Unprocessable Entity errors."""
    
    def __init__(self, 
                 message: str = "Unprocessable Entity",
                 validation_errors: Optional[Dict[str, list]] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="UNPROCESSABLE_ENTITY",
            status_code=422,
            **kwargs
        )
        self.validation_errors = validation_errors or {}
        
        if self.validation_errors:
            self.details['validation_errors'] = self.validation_errors


class TooManyRequestsError(APIError):
    """Exception for 429 Too Many Requests errors."""
    
    def __init__(self, 
                 message: str = "Too Many Requests",
                 retry_after: Optional[int] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="TOO_MANY_REQUESTS",
            status_code=429,
            **kwargs
        )
        self.retry_after = retry_after
        
        if retry_after:
            self.details['retry_after'] = retry_after


class InternalServerError(ServerError):
    """Exception for 500 Internal Server errors."""
    
    def __init__(self, 
                 message: str = "Internal Server Error",
                 **kwargs):
        super().__init__(
            message=message,
            error_code="INTERNAL_SERVER_ERROR",
            **kwargs
        )


class NotImplementedError(ServerError):
    """Exception for 501 Not Implemented errors."""
    
    def __init__(self, 
                 message: str = "Not Implemented",
                 **kwargs):
        super().__init__(
            message=message,
            error_code="NOT_IMPLEMENTED",
            status_code=501,
            **kwargs
        )


class BadGatewayError(ServerError):
    """Exception for 502 Bad Gateway errors."""
    
    def __init__(self, 
                 message: str = "Bad Gateway",
                 upstream_service: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="BAD_GATEWAY",
            status_code=502,
            **kwargs
        )
        self.upstream_service = upstream_service
        
        if upstream_service:
            self.details['upstream_service'] = upstream_service


class ServiceUnavailableError(ServerError):
    """Exception for 503 Service Unavailable errors."""
    
    def __init__(self, 
                 message: str = "Service Unavailable",
                 retry_after: Optional[int] = None,
                 maintenance_mode: bool = False,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="SERVICE_UNAVAILABLE",
            status_code=503,
            **kwargs
        )
        self.retry_after = retry_after
        self.maintenance_mode = maintenance_mode
        
        self.details.update({
            'retry_after': retry_after,
            'maintenance_mode': maintenance_mode
        })


class GatewayTimeoutError(ServerError):
    """Exception for 504 Gateway Timeout errors."""
    
    def __init__(self, 
                 message: str = "Gateway Timeout",
                 upstream_service: Optional[str] = None,
                 timeout_duration: Optional[int] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="GATEWAY_TIMEOUT",
            status_code=504,
            **kwargs
        )
        self.upstream_service = upstream_service
        self.timeout_duration = timeout_duration
        
        self.details.update({
            'upstream_service': upstream_service,
            'timeout_duration': timeout_duration
        })


class HTTPVersionNotSupportedError(ServerError):
    """Exception for 505 HTTP Version Not Supported errors."""
    
    def __init__(self, 
                 message: str = "HTTP Version Not Supported",
                 supported_versions: Optional[list] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="HTTP_VERSION_NOT_SUPPORTED",
            status_code=505,
            **kwargs
        )
        self.supported_versions = supported_versions or []
        
        if self.supported_versions:
            self.details['supported_versions'] = self.supported_versions


# JSON-specific errors

class InvalidJSONError(BadRequestError):
    """Exception for invalid JSON in request body."""
    
    def __init__(self, 
                 message: str = "Invalid JSON in request body",
                 json_error: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "INVALID_JSON"
        self.json_error = json_error
        
        if json_error:
            self.details['json_error'] = json_error


class MissingContentTypeError(BadRequestError):
    """Exception for missing or incorrect Content-Type header."""
    
    def __init__(self, 
                 message: str = "Missing or incorrect Content-Type header",
                 expected_type: str = "application/json",
                 received_type: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "MISSING_CONTENT_TYPE"
        self.expected_type = expected_type
        self.received_type = received_type
        
        self.details.update({
            'expected_type': expected_type,
            'received_type': received_type
        })


class PayloadTooLargeError(APIError):
    """Exception for 413 Payload Too Large errors."""
    
    def __init__(self, 
                 message: str = "Payload Too Large",
                 max_size: Optional[int] = None,
                 received_size: Optional[int] = None,
                 **kwargs):
        super().__init__(
            message=message,
            error_code="PAYLOAD_TOO_LARGE",
            status_code=413,
            **kwargs
        )
        self.max_size = max_size
        self.received_size = received_size
        
        self.details.update({
            'max_size': max_size,
            'received_size': received_size
        })