#!/usr/bin/env python3
"""
Core Validation Functions and Classes

Provides comprehensive input validation for all AgentShop modules.
Enhanced from the webshop validators with additional features and flexibility.
"""

import re
import os
from typing import Dict, List, Any, Optional, Union, Callable
from abc import ABC, abstractmethod

# Optional dependency - graceful fallback if not available
try:
    from email_validator import validate_email as email_validate, EmailNotValidError
    HAS_EMAIL_VALIDATOR = True
except ImportError:
    HAS_EMAIL_VALIDATOR = False


class BaseValidator(ABC):
    """Abstract base class for all validators."""
    
    def __init__(self, message: Optional[str] = None):
        self.message = message
    
    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate the value and return True if valid."""
        pass
    
    def get_error_message(self) -> str:
        """Get the error message for validation failure."""
        return self.message or "Validation failed"
    
    def __call__(self, value: Any) -> bool:
        """Allow validator to be called directly."""
        return self.validate(value)


class EmailValidator(BaseValidator):
    """Email address validator with comprehensive checks."""
    
    def __init__(self, 
                 message: Optional[str] = None,
                 check_deliverability: bool = True,
                 allow_international: bool = True):
        super().__init__(message or "Invalid email address")
        self.check_deliverability = check_deliverability
        self.allow_international = allow_international
    
    def validate(self, email: str) -> bool:
        """Validate email address format."""
        if not isinstance(email, str) or not email.strip():
            return False
        
        if HAS_EMAIL_VALIDATOR:
            try:
                email_validate(
                    email.strip(),
                    check_deliverability=self.check_deliverability
                )
                return True
            except EmailNotValidError:
                return False
        else:
            # Fallback regex validation
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            return bool(re.match(pattern, email.strip()))


class PasswordValidator(BaseValidator):
    """Password strength validator with configurable requirements."""
    
    def __init__(self,
                 min_length: int = 8,
                 max_length: int = 128,
                 require_lowercase: bool = True,
                 require_uppercase: bool = True,
                 require_numbers: bool = True,
                 require_special: bool = True,
                 special_chars: str = "!@#$%^&*(),.?\":{}|<>",
                 forbidden_passwords: Optional[List[str]] = None,
                 message: Optional[str] = None):
        super().__init__(message or "Password does not meet strength requirements")
        self.min_length = min_length
        self.max_length = max_length
        self.require_lowercase = require_lowercase
        self.require_uppercase = require_uppercase
        self.require_numbers = require_numbers
        self.require_special = require_special
        self.special_chars = special_chars
        self.forbidden_passwords = set(forbidden_passwords or [
            'password', '123456', 'qwerty', 'abc123', 'password123',
            'admin', 'letmein', 'welcome', 'monkey', '1234567890'
        ])
    
    def validate(self, password: str) -> bool:
        """Validate password strength."""
        errors = self.get_validation_errors(password)
        return len(errors) == 0
    
    def get_validation_errors(self, password: str) -> List[str]:
        """Get detailed validation errors for password."""
        if not isinstance(password, str):
            return ["Password must be a string"]
        
        errors = []
        
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        if len(password) > self.max_length:
            errors.append(f"Password must be no more than {self.max_length} characters long")
        
        if self.require_lowercase and not re.search(r"[a-z]", password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_uppercase and not re.search(r"[A-Z]", password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_numbers and not re.search(r"\d", password):
            errors.append("Password must contain at least one number")
        
        if self.require_special and not re.search(f"[{re.escape(self.special_chars)}]", password):
            errors.append(f"Password must contain at least one special character ({self.special_chars})")
        
        if password.lower() in self.forbidden_passwords:
            errors.append("Password is too common, please choose a stronger password")
        
        return errors


class PhoneValidator(BaseValidator):
    """Phone number validator with international format support."""
    
    def __init__(self,
                 allow_international: bool = True,
                 country_code: Optional[str] = None,
                 message: Optional[str] = None):
        super().__init__(message or "Invalid phone number format")
        self.allow_international = allow_international
        self.country_code = country_code
    
    def validate(self, phone: str) -> bool:
        """Validate phone number format."""
        if not isinstance(phone, str) or not phone.strip():
            return False
        
        # Remove all non-digit characters except + for international prefix
        cleaned = re.sub(r'[^\d+]', '', phone.strip())
        
        if self.allow_international:
            # International format: +[country code][number]
            pattern = r'^\+?1?\d{9,15}$'
        else:
            # National format (US): 10 digits
            pattern = r'^\d{10}$'
        
        return bool(re.match(pattern, cleaned))


class URLValidator(BaseValidator):
    """URL format validator with protocol and domain validation."""
    
    def __init__(self,
                 allowed_schemes: Optional[List[str]] = None,
                 require_tld: bool = True,
                 message: Optional[str] = None):
        super().__init__(message or "Invalid URL format")
        self.allowed_schemes = allowed_schemes or ['http', 'https']
        self.require_tld = require_tld
    
    def validate(self, url: str) -> bool:
        """Validate URL format."""
        if not isinstance(url, str) or not url.strip():
            return False
        
        url = url.strip()
        
        # Basic URL pattern
        if self.require_tld:
            pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        else:
            pattern = r'^https?:\/\/[-a-zA-Z0-9@:%._\+~#=]{1,256}([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
        
        if not re.match(pattern, url):
            return False
        
        # Check allowed schemes
        scheme = url.split('://')[0].lower()
        return scheme in self.allowed_schemes


class SlugValidator(BaseValidator):
    """URL slug validator for SEO-friendly URLs."""
    
    def __init__(self,
                 min_length: int = 1,
                 max_length: int = 100,
                 allow_underscores: bool = False,
                 message: Optional[str] = None):
        super().__init__(message or "Invalid slug format")
        self.min_length = min_length
        self.max_length = max_length
        self.allow_underscores = allow_underscores
    
    def validate(self, slug: str) -> bool:
        """Validate URL slug format."""
        if not isinstance(slug, str) or not slug.strip():
            return False
        
        slug = slug.strip()
        
        if len(slug) < self.min_length or len(slug) > self.max_length:
            return False
        
        if self.allow_underscores:
            pattern = r'^[a-z0-9]+(?:[-_][a-z0-9]+)*$'
        else:
            pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
        
        return bool(re.match(pattern, slug))


class FileValidator(BaseValidator):
    """File validation for uploads."""
    
    def __init__(self,
                 allowed_extensions: Optional[List[str]] = None,
                 max_size_mb: int = 10,
                 allowed_mime_types: Optional[List[str]] = None,
                 message: Optional[str] = None):
        super().__init__(message or "Invalid file")
        self.allowed_extensions = set(ext.lower() for ext in (allowed_extensions or []))
        self.max_size_mb = max_size_mb
        self.allowed_mime_types = set(allowed_mime_types or [])
    
    def validate_filename(self, filename: str) -> bool:
        """Validate file name and extension."""
        if not isinstance(filename, str) or not filename.strip():
            return False
        
        if not self.allowed_extensions:
            return True
        
        extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        return extension in self.allowed_extensions
    
    def validate_size(self, file_size: int) -> bool:
        """Validate file size in bytes."""
        max_size_bytes = self.max_size_mb * 1024 * 1024
        return file_size <= max_size_bytes
    
    def validate(self, file_info: Dict[str, Any]) -> bool:
        """Validate file information dictionary."""
        filename = file_info.get('filename', '')
        file_size = file_info.get('size', 0)
        mime_type = file_info.get('mime_type', '')
        
        if not self.validate_filename(filename):
            return False
        
        if not self.validate_size(file_size):
            return False
        
        if self.allowed_mime_types and mime_type not in self.allowed_mime_types:
            return False
        
        return True


# Convenience functions for backward compatibility and simple use cases

def validate_email(email: str) -> bool:
    """Validate email address format."""
    validator = EmailValidator()
    return validator.validate(email)


def validate_password_strength(password: str, min_length: int = 8) -> List[str]:
    """Validate password strength and return list of errors."""
    validator = PasswordValidator(min_length=min_length)
    return validator.get_validation_errors(password)


def validate_phone_number(phone: str) -> bool:
    """Validate phone number format."""
    validator = PhoneValidator()
    return validator.validate(phone)


def validate_url(url: str) -> bool:
    """Validate URL format."""
    validator = URLValidator()
    return validator.validate(url)


def validate_slug(slug: str) -> bool:
    """Validate URL slug format."""
    validator = SlugValidator()
    return validator.validate(slug)


def validate_image_file(filename: str) -> bool:
    """Validate image file extension."""
    validator = FileValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])
    return validator.validate_filename(filename)


def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """Validate file size."""
    validator = FileValidator(max_size_mb=max_size_mb)
    return validator.validate_size(file_size)


def sanitize_string(text: str, max_length: Optional[int] = None) -> str:
    """
    Sanitize string input by removing dangerous characters.
    
    Args:
        text: String to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not isinstance(text, str):
        return ""
    
    # Remove dangerous characters
    sanitized = re.sub(r'[<>"\'\&]', '', text)
    
    # Trim whitespace
    sanitized = sanitized.strip()
    
    # Truncate if needed
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


# Validator registry for dynamic validation

class ValidatorRegistry:
    """Registry for managing validators."""
    
    def __init__(self):
        self._validators: Dict[str, BaseValidator] = {}
    
    def register(self, name: str, validator: BaseValidator):
        """Register a validator."""
        self._validators[name] = validator
    
    def get(self, name: str) -> Optional[BaseValidator]:
        """Get a validator by name."""
        return self._validators.get(name)
    
    def validate(self, name: str, value: Any) -> bool:
        """Validate using a registered validator."""
        validator = self.get(name)
        if validator:
            return validator.validate(value)
        raise ValueError(f"Validator '{name}' not found")
    
    def list_validators(self) -> List[str]:
        """List all registered validator names."""
        return list(self._validators.keys())


# Global validator registry
validator_registry = ValidatorRegistry()

# Register default validators
validator_registry.register('email', EmailValidator())
validator_registry.register('password', PasswordValidator())
validator_registry.register('phone', PhoneValidator())
validator_registry.register('url', URLValidator())
validator_registry.register('slug', SlugValidator())
validator_registry.register('image', FileValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp']))


def get_validator(name: str) -> Optional[BaseValidator]:
    """Get a validator from the global registry."""
    return validator_registry.get(name)


def register_validator(name: str, validator: BaseValidator):
    """Register a validator in the global registry."""
    validator_registry.register(name, validator)