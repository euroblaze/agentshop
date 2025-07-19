#!/usr/bin/env python3
"""
API Validators - Input validation utilities
"""

import re
from typing import Dict, List, Any
from email_validator import validate_email as email_validate, EmailNotValidError


def validate_email(email: str) -> bool:
    """
    Validate email address format
    
    Args:
        email: Email address to validate
        
    Returns:
        True if valid email format
    """
    try:
        # Use email-validator library for comprehensive validation
        validated_email = email_validate(email)
        return True
    except EmailNotValidError:
        return False


def validate_password_strength(password: str, min_length: int = 8) -> List[str]:
    """
    Validate password strength requirements
    
    Args:
        password: Password to validate
        min_length: Minimum password length
        
    Returns:
        List of validation error messages
    """
    errors = []
    
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters long")
    
    if not re.search(r"[a-z]", password):
        errors.append("Password must contain at least one lowercase letter")
    
    if not re.search(r"[A-Z]", password):
        errors.append("Password must contain at least one uppercase letter")
    
    if not re.search(r"\d", password):
        errors.append("Password must contain at least one number")
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        errors.append("Password must contain at least one special character")
    
    # Check for common weak passwords
    weak_passwords = [
        'password', '123456', 'qwerty', 'abc123', 'password123',
        'admin', 'letmein', 'welcome', 'monkey', '1234567890'
    ]
    
    if password.lower() in weak_passwords:
        errors.append("Password is too common, please choose a stronger password")
    
    return errors


def validate_request_data(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, List[str]]:
    """
    Validate request data against JSON schema
    
    Args:
        data: Request data to validate
        schema: JSON schema definition
        
    Returns:
        Dictionary of validation errors
    """
    errors = {}
    
    # Basic validation implementation
    # In a real application, you'd use jsonschema library
    
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required fields
    for field in required_fields:
        if field not in data or data[field] is None:
            if field not in errors:
                errors[field] = []
            errors[field].append(f"{field} is required")
        elif isinstance(data[field], str) and not data[field].strip():
            if field not in errors:
                errors[field] = []
            errors[field].append(f"{field} cannot be empty")
    
    # Validate field types and constraints
    for field, value in data.items():
        if field in properties:
            field_schema = properties[field]
            field_errors = _validate_field(field, value, field_schema)
            if field_errors:
                errors[field] = field_errors
    
    return errors


def _validate_field(field_name: str, value: Any, field_schema: Dict[str, Any]) -> List[str]:
    """Validate individual field against schema"""
    errors = []
    field_type = field_schema.get('type')
    
    # Type validation
    if field_type == 'string' and not isinstance(value, str):
        errors.append(f"{field_name} must be a string")
    elif field_type == 'integer' and not isinstance(value, int):
        errors.append(f"{field_name} must be an integer")
    elif field_type == 'number' and not isinstance(value, (int, float)):
        errors.append(f"{field_name} must be a number")
    elif field_type == 'boolean' and not isinstance(value, bool):
        errors.append(f"{field_name} must be a boolean")
    
    # String constraints
    if field_type == 'string' and isinstance(value, str):
        min_length = field_schema.get('minLength')
        max_length = field_schema.get('maxLength')
        pattern = field_schema.get('pattern')
        
        if min_length and len(value) < min_length:
            errors.append(f"{field_name} must be at least {min_length} characters")
        
        if max_length and len(value) > max_length:
            errors.append(f"{field_name} must be no more than {max_length} characters")
        
        if pattern and not re.match(pattern, value):
            errors.append(f"{field_name} format is invalid")
    
    # Number constraints
    if field_type in ['integer', 'number'] and isinstance(value, (int, float)):
        minimum = field_schema.get('minimum')
        maximum = field_schema.get('maximum')
        
        if minimum is not None and value < minimum:
            errors.append(f"{field_name} must be at least {minimum}")
        
        if maximum is not None and value > maximum:
            errors.append(f"{field_name} must be no more than {maximum}")
    
    # Enum validation
    enum_values = field_schema.get('enum')
    if enum_values and value not in enum_values:
        errors.append(f"{field_name} must be one of: {', '.join(map(str, enum_values))}")
    
    return errors


def validate_phone_number(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if valid phone number format
    """
    # Basic phone number validation (international format)
    pattern = r'^\+?1?\d{9,15}$'
    return bool(re.match(pattern, re.sub(r'[^\d+]', '', phone)))


def validate_url(url: str) -> bool:
    """
    Validate URL format
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid URL format
    """
    pattern = r'^https?:\/\/(www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_\+.~#?&//=]*)$'
    return bool(re.match(pattern, url))


def validate_slug(slug: str) -> bool:
    """
    Validate URL slug format
    
    Args:
        slug: URL slug to validate
        
    Returns:
        True if valid slug format
    """
    pattern = r'^[a-z0-9]+(?:-[a-z0-9]+)*$'
    return bool(re.match(pattern, slug))


def sanitize_string(text: str, max_length: int = None) -> str:
    """
    Sanitize string input
    
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


def validate_image_file(filename: str) -> bool:
    """
    Validate image file extension
    
    Args:
        filename: Image filename to validate
        
    Returns:
        True if valid image file
    """
    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif', 'webp'}
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    return extension in allowed_extensions


def validate_file_size(file_size: int, max_size_mb: int = 10) -> bool:
    """
    Validate file size
    
    Args:
        file_size: File size in bytes
        max_size_mb: Maximum size in MB
        
    Returns:
        True if file size is acceptable
    """
    max_size_bytes = max_size_mb * 1024 * 1024
    return file_size <= max_size_bytes