#!/usr/bin/env python3
"""
Data Sanitization Utilities

Provides functions for cleaning and sanitizing user input to prevent
security vulnerabilities and ensure data consistency.
"""

import re
import html
import os
from typing import Optional, Dict, Any, List
from urllib.parse import quote, unquote


def sanitize_html(text: str, 
                  allowed_tags: Optional[List[str]] = None,
                  strip_dangerous: bool = True) -> str:
    """
    Sanitize HTML content by removing or escaping dangerous elements.
    
    Args:
        text: HTML text to sanitize
        allowed_tags: List of allowed HTML tags (None = escape all)
        strip_dangerous: Whether to strip dangerous attributes
        
    Returns:
        Sanitized HTML text
    """
    if not isinstance(text, str):
        return ""
    
    if allowed_tags is None:
        # Escape all HTML
        return html.escape(text)
    
    # Basic HTML sanitization (for production, use bleach library)
    # Remove script tags and dangerous attributes
    if strip_dangerous:
        # Remove script tags
        text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove dangerous attributes
        dangerous_attrs = ['onclick', 'onload', 'onerror', 'onmouseover', 'onmouseout', 'onfocus', 'onblur']
        for attr in dangerous_attrs:
            text = re.sub(f'{attr}\\s*=\\s*["\'][^"\']*["\']', '', text, flags=re.IGNORECASE)
    
    # If specific tags are allowed, implement tag filtering here
    # For production use, consider using the bleach library
    
    return text


def sanitize_filename(filename: str, 
                     max_length: int = 255,
                     replacement_char: str = '_') -> str:
    """
    Sanitize filename by removing dangerous characters.
    
    Args:
        filename: Original filename
        max_length: Maximum filename length
        replacement_char: Character to replace invalid chars with
        
    Returns:
        Sanitized filename
    """
    if not isinstance(filename, str):
        return "untitled"
    
    # Remove path separators and dangerous characters
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(dangerous_chars, replacement_char, filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Ensure it's not empty
    if not sanitized:
        sanitized = "untitled"
    
    # Truncate if too long, preserving extension
    if len(sanitized) > max_length:
        if '.' in sanitized:
            name, ext = sanitized.rsplit('.', 1)
            max_name_length = max_length - len(ext) - 1
            sanitized = name[:max_name_length] + '.' + ext
        else:
            sanitized = sanitized[:max_length]
    
    return sanitized


def sanitize_path(path: str, 
                  allow_absolute: bool = False,
                  max_length: int = 4096) -> str:
    """
    Sanitize file path to prevent directory traversal attacks.
    
    Args:
        path: File path to sanitize
        allow_absolute: Whether to allow absolute paths
        max_length: Maximum path length
        
    Returns:
        Sanitized path
    """
    if not isinstance(path, str):
        return ""
    
    # Normalize path separators
    path = path.replace('\\', '/')
    
    # Remove dangerous sequences
    path = re.sub(r'\.\./', '', path)  # Remove ../ sequences
    path = re.sub(r'/\.\.', '', path)  # Remove /.. sequences
    path = re.sub(r'//+', '/', path)   # Remove multiple slashes
    
    # Handle absolute paths
    if not allow_absolute and path.startswith('/'):
        path = path.lstrip('/')
    
    # Remove null bytes and control characters
    path = re.sub(r'[\x00-\x1f]', '', path)
    
    # Truncate if too long
    if len(path) > max_length:
        path = path[:max_length]
    
    return path


def strip_dangerous_chars(text: str, 
                         additional_chars: str = "",
                         replacement: str = "") -> str:
    """
    Strip dangerous characters from text.
    
    Args:
        text: Text to clean
        additional_chars: Additional characters to remove
        replacement: Character to replace dangerous chars with
        
    Returns:
        Cleaned text
    """
    if not isinstance(text, str):
        return ""
    
    # Common dangerous characters
    dangerous = r'[<>"\'\&\x00-\x1f\x7f-\x9f]' + re.escape(additional_chars)
    
    return re.sub(dangerous, replacement, text)


def normalize_whitespace(text: str, 
                        preserve_newlines: bool = False,
                        max_consecutive_spaces: int = 1) -> str:
    """
    Normalize whitespace in text.
    
    Args:
        text: Text to normalize
        preserve_newlines: Whether to preserve line breaks
        max_consecutive_spaces: Maximum consecutive spaces allowed
        
    Returns:
        Text with normalized whitespace
    """
    if not isinstance(text, str):
        return ""
    
    # Replace tabs with spaces
    text = text.replace('\t', ' ')
    
    # Remove carriage returns
    text = text.replace('\r', '')
    
    if preserve_newlines:
        # Normalize spaces but keep newlines
        lines = text.split('\n')
        normalized_lines = []
        
        for line in lines:
            # Collapse multiple spaces
            line = re.sub(r' {2,}', ' ' * max_consecutive_spaces, line)
            # Strip leading/trailing whitespace
            line = line.strip()
            normalized_lines.append(line)
        
        text = '\n'.join(normalized_lines)
    else:
        # Replace all whitespace with single spaces
        text = re.sub(r'\s+', ' ', text)
        # Strip leading/trailing whitespace
        text = text.strip()
    
    return text


def sanitize_sql_identifier(identifier: str) -> str:
    """
    Sanitize SQL identifier (table name, column name, etc.).
    
    Args:
        identifier: SQL identifier to sanitize
        
    Returns:
        Sanitized identifier safe for SQL
    """
    if not isinstance(identifier, str):
        return ""
    
    # Only allow alphanumeric characters and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', identifier)
    
    # Ensure it starts with a letter or underscore
    if sanitized and not re.match(r'^[a-zA-Z_]', sanitized):
        sanitized = '_' + sanitized
    
    # Limit length
    if len(sanitized) > 63:  # PostgreSQL limit
        sanitized = sanitized[:63]
    
    return sanitized


def sanitize_email(email: str) -> str:
    """
    Basic email sanitization.
    
    Args:
        email: Email address to sanitize
        
    Returns:
        Sanitized email address
    """
    if not isinstance(email, str):
        return ""
    
    # Convert to lowercase and strip whitespace
    email = email.lower().strip()
    
    # Remove dangerous characters (basic sanitization)
    email = re.sub(r'[<>"\'\&\x00-\x1f]', '', email)
    
    return email


def sanitize_phone(phone: str) -> str:
    """
    Sanitize phone number by keeping only digits and + sign.
    
    Args:
        phone: Phone number to sanitize
        
    Returns:
        Sanitized phone number
    """
    if not isinstance(phone, str):
        return ""
    
    # Keep only digits, +, and some common separators temporarily
    phone = re.sub(r'[^\d+\-\(\)\s\.]', '', phone)
    
    # Remove separators, keep only digits and leading +
    if phone.startswith('+'):
        phone = '+' + re.sub(r'[^\d]', '', phone[1:])
    else:
        phone = re.sub(r'[^\d]', '', phone)
    
    return phone


def sanitize_url(url: str, 
                allowed_schemes: Optional[List[str]] = None) -> str:
    """
    Sanitize URL by validating scheme and encoding.
    
    Args:
        url: URL to sanitize
        allowed_schemes: List of allowed URL schemes
        
    Returns:
        Sanitized URL
    """
    if not isinstance(url, str):
        return ""
    
    if allowed_schemes is None:
        allowed_schemes = ['http', 'https']
    
    url = url.strip()
    
    # Check if URL has a scheme
    if '://' not in url:
        url = 'https://' + url
    
    # Extract scheme
    scheme = url.split('://')[0].lower()
    
    # Validate scheme
    if scheme not in allowed_schemes:
        return ""
    
    # Basic URL encoding for safety
    # In production, use urllib.parse for proper URL handling
    
    return url


def sanitize_json_string(text: str) -> str:
    """
    Sanitize string for safe inclusion in JSON.
    
    Args:
        text: Text to sanitize
        
    Returns:
        JSON-safe string
    """
    if not isinstance(text, str):
        return ""
    
    # Escape JSON special characters
    replacements = {
        '"': '\\"',
        '\\': '\\\\',
        '\b': '\\b',
        '\f': '\\f',
        '\n': '\\n',
        '\r': '\\r',
        '\t': '\\t'
    }
    
    for char, escape in replacements.items():
        text = text.replace(char, escape)
    
    # Remove control characters
    text = re.sub(r'[\x00-\x1f\x7f]', '', text)
    
    return text


def sanitize_css_value(value: str) -> str:
    """
    Sanitize CSS value to prevent CSS injection.
    
    Args:
        value: CSS value to sanitize
        
    Returns:
        Sanitized CSS value
    """
    if not isinstance(value, str):
        return ""
    
    # Remove potentially dangerous CSS functions and properties
    dangerous_patterns = [
        r'expression\s*\(',  # IE expression()
        r'javascript\s*:',   # javascript: URLs
        r'@import',          # @import rules
        r'url\s*\(',         # url() functions (could be dangerous)
        r'behavior\s*:',     # IE behavior property
    ]
    
    value_lower = value.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, value_lower):
            return ""
    
    # Remove control characters
    value = re.sub(r'[\x00-\x1f\x7f]', '', value)
    
    return value


class TextSanitizer:
    """Configurable text sanitizer with multiple cleaning options."""
    
    def __init__(self,
                 strip_html: bool = True,
                 normalize_whitespace: bool = True,
                 max_length: Optional[int] = None,
                 allowed_chars: Optional[str] = None,
                 forbidden_chars: Optional[str] = None):
        self.strip_html = strip_html
        self.normalize_whitespace = normalize_whitespace
        self.max_length = max_length
        self.allowed_chars = allowed_chars
        self.forbidden_chars = forbidden_chars
    
    def sanitize(self, text: str) -> str:
        """Sanitize text according to configuration."""
        if not isinstance(text, str):
            return ""
        
        # Strip HTML if configured
        if self.strip_html:
            text = html.escape(text)
        
        # Apply character filtering
        if self.allowed_chars:
            # Keep only allowed characters
            text = re.sub(f'[^{re.escape(self.allowed_chars)}]', '', text)
        elif self.forbidden_chars:
            # Remove forbidden characters
            text = re.sub(f'[{re.escape(self.forbidden_chars)}]', '', text)
        else:
            # Default: remove dangerous characters
            text = strip_dangerous_chars(text)
        
        # Normalize whitespace if configured
        if self.normalize_whitespace:
            text = normalize_whitespace(text)
        
        # Truncate if max length specified
        if self.max_length and len(text) > self.max_length:
            text = text[:self.max_length]
        
        return text


# Predefined sanitizers for common use cases

html_sanitizer = TextSanitizer(strip_html=True, normalize_whitespace=True)
filename_sanitizer = TextSanitizer(
    strip_html=True,
    normalize_whitespace=True,
    forbidden_chars='<>:"/\\|?*\x00-\x1f'
)
alphanumeric_sanitizer = TextSanitizer(
    strip_html=True,
    normalize_whitespace=True,
    allowed_chars='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 '
)


def get_sanitizer(sanitizer_type: str) -> TextSanitizer:
    """
    Get a predefined sanitizer by type.
    
    Args:
        sanitizer_type: Type of sanitizer ('html', 'filename', 'alphanumeric')
        
    Returns:
        TextSanitizer instance
    """
    sanitizers = {
        'html': html_sanitizer,
        'filename': filename_sanitizer,
        'alphanumeric': alphanumeric_sanitizer
    }
    
    return sanitizers.get(sanitizer_type, html_sanitizer)