"""
Core Validation Module

Provides unified input validation and sanitization across all AgentShop modules.
"""

from .validators import (
    validate_email,
    validate_password_strength,
    validate_phone_number,
    validate_url,
    validate_slug,
    validate_image_file,
    validate_file_size,
    sanitize_string,
    EmailValidator,
    PasswordValidator,
    PhoneValidator,
    URLValidator,
    SlugValidator,
    FileValidator
)

from .schemas import (
    validate_request_data,
    JSONSchemaValidator,
    create_schema,
    validate_field
)

from .sanitizers import (
    sanitize_html,
    sanitize_filename,
    sanitize_path,
    strip_dangerous_chars,
    normalize_whitespace
)

__all__ = [
    # Validation functions
    'validate_email',
    'validate_password_strength',
    'validate_phone_number',
    'validate_url',
    'validate_slug',
    'validate_image_file',
    'validate_file_size',
    'sanitize_string',
    
    # Validator classes
    'EmailValidator',
    'PasswordValidator',
    'PhoneValidator',
    'URLValidator',
    'SlugValidator',
    'FileValidator',
    
    # Schema validation
    'validate_request_data',
    'JSONSchemaValidator',
    'create_schema',
    'validate_field',
    
    # Sanitization
    'sanitize_html',
    'sanitize_filename',
    'sanitize_path',
    'strip_dangerous_chars',
    'normalize_whitespace'
]