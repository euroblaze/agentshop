#!/usr/bin/env python3
"""
Authentication Security - Enhanced security for user authentication
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from flask import current_app
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token
import bcrypt
import logging

logger = logging.getLogger(__name__)


class PasswordSecurity:
    """Enhanced password security utilities"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password with bcrypt and salt"""
        # Generate salt and hash password
        salt = bcrypt.gensalt(rounds=12)  # Higher rounds for better security
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify password against hash"""
        try:
            return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        errors = []
        score = 0
        
        # Length check
        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")
        elif len(password) >= 12:
            score += 2
        else:
            score += 1
        
        # Character variety checks
        if not re.search(r'[a-z]', password):
            errors.append("Password must contain lowercase letters")
        else:
            score += 1
            
        if not re.search(r'[A-Z]', password):
            errors.append("Password must contain uppercase letters")
        else:
            score += 1
            
        if not re.search(r'\d', password):
            errors.append("Password must contain numbers")
        else:
            score += 1
            
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain special characters")
        else:
            score += 2
        
        # Common password check
        common_passwords = [
            'password', '123456', '123456789', 'qwerty', 'abc123',
            'password123', 'admin', 'letmein', 'welcome', 'monkey'
        ]
        if password.lower() in common_passwords:
            errors.append("Password is too common")
            score = 0
        
        # Determine strength
        if score >= 6:
            strength = 'strong'
        elif score >= 4:
            strength = 'medium'
        else:
            strength = 'weak'
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'strength': strength,
            'score': score
        }


class TokenSecurity:
    """Enhanced JWT token security"""
    
    @staticmethod
    def create_secure_tokens(identity: str, additional_claims: Dict = None) -> Dict[str, str]:
        """Create secure access and refresh tokens"""
        
        # Short-lived access token (15 minutes)
        access_token = create_access_token(
            identity=identity,
            expires_delta=timedelta(minutes=15),
            additional_claims=additional_claims or {}
        )
        
        # Longer-lived refresh token (7 days)
        refresh_token = create_refresh_token(
            identity=identity,
            expires_delta=timedelta(days=7)
        )
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'expires_in': 900,  # 15 minutes in seconds
            'token_type': 'Bearer'
        }
    
    @staticmethod
    def is_token_blacklisted(jti: str) -> bool:
        """Check if token is blacklisted (implement with Redis/database)"""
        # TODO: Implement with Redis or database storage
        # For now, return False - implement proper blacklist storage
        return False
    
    @staticmethod
    def blacklist_token(jti: str, expires_at: datetime) -> bool:
        """Add token to blacklist"""
        # TODO: Implement with Redis or database storage
        # Store token JTI with expiration time
        logger.info(f"Token {jti} blacklisted until {expires_at}")
        return True


class SessionSecurity:
    """Session security management"""
    
    @staticmethod
    def generate_session_id() -> str:
        """Generate cryptographically secure session ID"""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_csrf_token() -> str:
        """Generate CSRF token"""
        return secrets.token_hex(32)
    
    @staticmethod
    def validate_session_security(request_data: Dict) -> Dict[str, Any]:
        """Validate session security parameters"""
        issues = []
        
        # Check for suspicious login patterns
        if 'user_agent' in request_data:
            ua = request_data['user_agent'].lower()
            if 'bot' in ua or 'crawler' in ua or 'spider' in ua:
                issues.append("Suspicious user agent detected")
        
        # Check for rapid login attempts
        if 'ip_address' in request_data:
            # TODO: Implement rate limiting check
            pass
        
        return {
            'secure': len(issues) == 0,
            'issues': issues
        }


class InputSanitization:
    """Input sanitization and validation"""
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """Sanitize email input"""
        if not email:
            return ""
        
        # Convert to lowercase and strip whitespace
        email = email.lower().strip()
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            raise ValueError("Invalid email format")
        
        return email
    
    @staticmethod
    def sanitize_string(input_str: str, max_length: int = 255) -> str:
        """Sanitize string input"""
        if not input_str:
            return ""
        
        # Strip whitespace and limit length
        sanitized = input_str.strip()[:max_length]
        
        # Remove potentially dangerous characters
        dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
        for char in dangerous_chars:
            sanitized = sanitized.replace(char, '')
        
        return sanitized
    
    @staticmethod
    def validate_phone_number(phone: str) -> str:
        """Validate and sanitize phone number"""
        if not phone:
            return ""
        
        # Remove all non-digit characters except +
        cleaned = re.sub(r'[^\d+]', '', phone)
        
        # Validate format
        if not re.match(r'^\+?[\d]{10,15}$', cleaned):
            raise ValueError("Invalid phone number format")
        
        return cleaned


class SecurityHeaders:
    """Security headers for HTTP responses"""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get recommended security headers"""
        return {
            # Prevent clickjacking
            'X-Frame-Options': 'DENY',
            
            # Prevent MIME type sniffing
            'X-Content-Type-Options': 'nosniff',
            
            # XSS protection
            'X-XSS-Protection': '1; mode=block',
            
            # Strict transport security (HTTPS only)
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            
            # Content Security Policy
            'Content-Security-Policy': (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            ),
            
            # Referrer policy
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            
            # Permissions policy
            'Permissions-Policy': (
                "geolocation=(), microphone=(), camera=(), "
                "payment=(), usb=(), magnetometer=(), gyroscope=()"
            )
        }


class DataEncryption:
    """Data encryption utilities"""
    
    @staticmethod
    def encrypt_sensitive_data(data: str, key: Optional[str] = None) -> str:
        """Encrypt sensitive data (PII, payment info)"""
        # TODO: Implement with cryptography library
        # For now, return base64 encoded (NOT secure - implement proper encryption)
        import base64
        return base64.b64encode(data.encode()).decode()
    
    @staticmethod
    def decrypt_sensitive_data(encrypted_data: str, key: Optional[str] = None) -> str:
        """Decrypt sensitive data"""
        # TODO: Implement with cryptography library
        import base64
        return base64.b64decode(encrypted_data.encode()).decode()
    
    @staticmethod
    def hash_pii(data: str) -> str:
        """Hash PII for search/indexing while preserving privacy"""
        return hashlib.sha256(data.encode()).hexdigest()


# Security configuration constants
SECURITY_CONFIG = {
    'PASSWORD_MIN_LENGTH': 8,
    'PASSWORD_MAX_LENGTH': 128,
    'LOGIN_ATTEMPT_LIMIT': 5,
    'LOGIN_ATTEMPT_WINDOW': 300,  # 5 minutes
    'SESSION_TIMEOUT': 1800,  # 30 minutes
    'TOKEN_BLACKLIST_TTL': 86400,  # 24 hours
    'CSRF_TOKEN_TTL': 3600,  # 1 hour
}