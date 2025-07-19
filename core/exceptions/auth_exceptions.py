#!/usr/bin/env python3
"""
Authentication and Authorization Exceptions

Specialized exceptions for JWT and authentication-related errors.
"""

from typing import Optional, Dict, Any
from .base_exceptions import AuthenticationError, AuthorizationError


class TokenExpiredError(AuthenticationError):
    """Exception raised when JWT token has expired."""
    
    def __init__(self, 
                 message: str = "Token has expired",
                 token_type: str = "access",
                 expired_at: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "TOKEN_EXPIRED"
        self.token_type = token_type
        self.expired_at = expired_at
        
        self.details.update({
            'token_type': token_type,
            'expired_at': expired_at
        })


class InvalidTokenError(AuthenticationError):
    """Exception raised when JWT token is invalid."""
    
    def __init__(self, 
                 message: str = "Invalid token",
                 token_error: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "INVALID_TOKEN"
        self.token_error = token_error
        
        if token_error:
            self.details['token_error'] = token_error


class TokenRequiredError(AuthenticationError):
    """Exception raised when authorization token is required but missing."""
    
    def __init__(self, 
                 message: str = "Authorization token required",
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "TOKEN_REQUIRED"


class FreshTokenRequiredError(AuthenticationError):
    """Exception raised when a fresh token is required."""
    
    def __init__(self, 
                 message: str = "Fresh token required",
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "FRESH_TOKEN_REQUIRED"


class TokenRevokedError(AuthenticationError):
    """Exception raised when JWT token has been revoked."""
    
    def __init__(self, 
                 message: str = "Token has been revoked",
                 revoked_at: Optional[str] = None,
                 revocation_reason: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "TOKEN_REVOKED"
        self.revoked_at = revoked_at
        self.revocation_reason = revocation_reason
        
        self.details.update({
            'revoked_at': revoked_at,
            'revocation_reason': revocation_reason
        })


class SessionExpiredError(AuthenticationError):
    """Exception raised when user session has expired."""
    
    def __init__(self, 
                 message: str = "Session has expired",
                 session_id: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "SESSION_EXPIRED"
        self.session_id = session_id
        
        if session_id:
            self.details['session_id'] = session_id


class InvalidCredentialsError(AuthenticationError):
    """Exception raised when login credentials are invalid."""
    
    def __init__(self, 
                 message: str = "Invalid credentials",
                 credential_type: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "INVALID_CREDENTIALS"
        self.credential_type = credential_type
        
        if credential_type:
            self.details['credential_type'] = credential_type


class AccountLockedError(AuthenticationError):
    """Exception raised when user account is locked."""
    
    def __init__(self, 
                 message: str = "Account is locked",
                 locked_until: Optional[str] = None,
                 lock_reason: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "ACCOUNT_LOCKED"
        self.locked_until = locked_until
        self.lock_reason = lock_reason
        
        self.details.update({
            'locked_until': locked_until,
            'lock_reason': lock_reason
        })


class AccountDisabledError(AuthenticationError):
    """Exception raised when user account is disabled."""
    
    def __init__(self, 
                 message: str = "Account is disabled",
                 disabled_reason: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "ACCOUNT_DISABLED"
        self.disabled_reason = disabled_reason
        
        if disabled_reason:
            self.details['disabled_reason'] = disabled_reason


class InsufficientPermissionsError(AuthorizationError):
    """Exception raised when user lacks required permissions."""
    
    def __init__(self, 
                 message: str = "Insufficient permissions",
                 required_permissions: Optional[list] = None,
                 user_permissions: Optional[list] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "INSUFFICIENT_PERMISSIONS"
        self.required_permissions = required_permissions or []
        self.user_permissions = user_permissions or []
        
        self.details.update({
            'required_permissions': self.required_permissions,
            'user_permissions': self.user_permissions
        })


class RoleRequiredError(AuthorizationError):
    """Exception raised when a specific role is required."""
    
    def __init__(self, 
                 message: str = "Required role not found",
                 required_roles: Optional[list] = None,
                 user_roles: Optional[list] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "ROLE_REQUIRED"
        self.required_roles = required_roles or []
        self.user_roles = user_roles or []
        
        self.details.update({
            'required_roles': self.required_roles,
            'user_roles': self.user_roles
        })


class AdminRequiredError(AuthorizationError):
    """Exception raised when admin privileges are required."""
    
    def __init__(self, 
                 message: str = "Administrator privileges required",
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "ADMIN_REQUIRED"


class ResourceOwnershipError(AuthorizationError):
    """Exception raised when user doesn't own the requested resource."""
    
    def __init__(self, 
                 message: str = "You don't have access to this resource",
                 resource_type: Optional[str] = None,
                 resource_id: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "RESOURCE_OWNERSHIP_ERROR"
        self.resource_type = resource_type
        self.resource_id = resource_id
        
        self.details.update({
            'resource_type': resource_type,
            'resource_id': resource_id
        })