#!/usr/bin/env python3
"""
Security Middleware - Comprehensive security middleware for Flask application
"""

import time
import json
import logging
from functools import wraps
from typing import Dict, Any, Optional, Callable
from flask import Flask, request, jsonify, g, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from datetime import datetime, timedelta
import redis
import hashlib
import re

logger = logging.getLogger(__name__)


class SecurityMiddleware:
    """Comprehensive security middleware"""
    
    def __init__(self, app: Flask = None, redis_client=None):
        self.app = app
        self.redis_client = redis_client
        self.limiter = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize security middleware with Flask app"""
        self.app = app
        
        # Initialize rate limiter
        self.limiter = Limiter(
            app,
            key_func=get_remote_address,
            storage_uri=app.config.get('REDIS_URL', 'memory://'),
            default_limits=["1000 per hour", "100 per minute"]
        )
        
        # Register middleware
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Register error handlers
        app.errorhandler(429)(self.rate_limit_handler)
        app.errorhandler(403)(self.forbidden_handler)
    
    def before_request(self):
        """Execute before each request"""
        g.start_time = time.time()
        
        # Security checks
        if not self.validate_request_security():
            return jsonify({'error': 'Request blocked for security reasons'}), 403
        
        # Rate limiting for sensitive endpoints
        if self.is_sensitive_endpoint():
            if not self.check_enhanced_rate_limit():
                return jsonify({'error': 'Rate limit exceeded'}), 429
        
        # CSRF protection for state-changing operations
        if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
            if not self.validate_csrf_token():
                return jsonify({'error': 'CSRF token validation failed'}), 403
    
    def after_request(self, response):
        """Execute after each request"""
        # Add security headers
        security_headers = self.get_security_headers()
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Log security events
        self.log_security_event(response)
        
        return response
    
    def validate_request_security(self) -> bool:
        """Validate request for security threats"""
        
        # Check for SQL injection patterns
        if self.contains_sql_injection():
            logger.warning(f"SQL injection attempt from {request.remote_addr}")
            return False
        
        # Check for XSS patterns
        if self.contains_xss_patterns():
            logger.warning(f"XSS attempt from {request.remote_addr}")
            return False
        
        # Check for suspicious user agents
        if self.is_suspicious_user_agent():
            logger.warning(f"Suspicious user agent from {request.remote_addr}")
            return False
        
        # Check request size
        if self.is_request_too_large():
            logger.warning(f"Oversized request from {request.remote_addr}")
            return False
        
        return True
    
    def contains_sql_injection(self) -> bool:
        """Check for SQL injection patterns"""
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+['\"][^'\"]*['\"])",
            r"(--|/\*|\*/|;)",
            r"(\bxp_cmdshell\b)",
            r"(\bsp_executesql\b)"
        ]
        
        # Check all request data
        data_to_check = []
        
        # URL parameters
        for key, value in request.args.items():
            data_to_check.extend([key, value])
        
        # Form data
        if request.form:
            for key, value in request.form.items():
                data_to_check.extend([key, value])
        
        # JSON data
        if request.is_json and request.json:
            data_to_check.append(json.dumps(request.json))
        
        # Check patterns
        for data in data_to_check:
            if isinstance(data, str):
                for pattern in sql_patterns:
                    if re.search(pattern, data, re.IGNORECASE):
                        return True
        
        return False
    
    def contains_xss_patterns(self) -> bool:
        """Check for XSS attack patterns"""
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<embed[^>]*>",
            r"<object[^>]*>",
            r"eval\s*\(",
            r"expression\s*\("
        ]
        
        # Check all string inputs
        data_to_check = []
        
        for key, value in request.args.items():
            data_to_check.extend([key, value])
        
        if request.form:
            for key, value in request.form.items():
                data_to_check.extend([key, value])
        
        if request.is_json and request.json:
            data_to_check.append(json.dumps(request.json))
        
        for data in data_to_check:
            if isinstance(data, str):
                for pattern in xss_patterns:
                    if re.search(pattern, data, re.IGNORECASE):
                        return True
        
        return False
    
    def is_suspicious_user_agent(self) -> bool:
        """Check for suspicious user agents"""
        user_agent = request.headers.get('User-Agent', '').lower()
        
        suspicious_patterns = [
            'bot', 'crawler', 'spider', 'scraper', 'curl', 'wget',
            'python-requests', 'postman', 'insomnia', 'nikto',
            'sqlmap', 'nmap', 'masscan', 'zap', 'burp'
        ]
        
        # Allow legitimate search engine bots
        allowed_bots = [
            'googlebot', 'bingbot', 'slurp', 'duckduckbot',
            'baiduspider', 'yandexbot', 'facebookexternalhit'
        ]
        
        # Check if it's an allowed bot first
        for allowed in allowed_bots:
            if allowed in user_agent:
                return False
        
        # Check for suspicious patterns
        for pattern in suspicious_patterns:
            if pattern in user_agent:
                return True
        
        # Check for empty or very short user agents
        if len(user_agent) < 10:
            return True
        
        return False
    
    def is_request_too_large(self) -> bool:
        """Check if request payload is suspiciously large"""
        content_length = request.content_length
        if content_length:
            max_size = current_app.config.get('MAX_CONTENT_LENGTH', 16 * 1024 * 1024)  # 16MB
            return content_length > max_size
        return False
    
    def is_sensitive_endpoint(self) -> bool:
        """Check if current endpoint is security-sensitive"""
        sensitive_patterns = [
            r'/api/auth/',
            r'/api/admin/',
            r'/api/payments/',
            r'/api/orders/',
            r'/api/customers/\d+',
        ]
        
        path = request.path
        for pattern in sensitive_patterns:
            if re.match(pattern, path):
                return True
        
        return False
    
    def check_enhanced_rate_limit(self) -> bool:
        """Enhanced rate limiting for sensitive endpoints"""
        if not self.redis_client:
            return True  # Skip if Redis not available
        
        ip = request.remote_addr
        endpoint = request.endpoint or request.path
        
        # Different limits for different endpoints
        limits = {
            'auth.login': {'count': 5, 'window': 300},  # 5 attempts per 5 minutes
            'auth.register': {'count': 3, 'window': 3600},  # 3 per hour
            'payments': {'count': 10, 'window': 600},  # 10 per 10 minutes
            'default': {'count': 60, 'window': 60}  # 60 per minute
        }
        
        # Get appropriate limit
        limit_key = endpoint if endpoint in limits else 'default'
        limit = limits[limit_key]
        
        # Redis key for rate limiting
        redis_key = f"rate_limit:{ip}:{endpoint}"
        
        try:
            current_count = self.redis_client.get(redis_key)
            if current_count is None:
                # First request
                self.redis_client.setex(redis_key, limit['window'], 1)
                return True
            
            current_count = int(current_count)
            if current_count >= limit['count']:
                return False
            
            # Increment counter
            self.redis_client.incr(redis_key)
            return True
            
        except Exception as e:
            logger.error(f"Rate limiting error: {e}")
            return True  # Allow request if Redis fails
    
    def validate_csrf_token(self) -> bool:
        """Validate CSRF token for state-changing operations"""
        # Skip CSRF for API calls with valid JWT
        if request.headers.get('Authorization'):
            return True
        
        # Skip for certain content types
        if request.content_type and 'application/json' in request.content_type:
            return True
        
        csrf_token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        session_token = request.cookies.get('csrf_token')
        
        if not csrf_token or not session_token:
            return False
        
        return csrf_token == session_token
    
    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers for response"""
        return {
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'Content-Security-Policy': self.get_csp_header(),
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()',
            'X-Request-ID': self.generate_request_id()
        }
    
    def get_csp_header(self) -> str:
        """Generate Content Security Policy header"""
        # Adjust CSP based on environment
        if current_app.config.get('DEBUG'):
            # More permissive CSP for development
            return (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval' https:; "
                "style-src 'self' 'unsafe-inline' https:; "
                "img-src 'self' data: https:; "
                "font-src 'self' https:; "
                "connect-src 'self' https: ws: wss:; "
                "frame-ancestors 'none';"
            )
        else:
            # Stricter CSP for production
            return (
                "default-src 'self'; "
                "script-src 'self'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self'; "
                "connect-src 'self' https:; "
                "frame-ancestors 'none';"
            )
    
    def generate_request_id(self) -> str:
        """Generate unique request ID for tracking"""
        import uuid
        return str(uuid.uuid4())
    
    def log_security_event(self, response):
        """Log security-related events"""
        duration = time.time() - g.start_time
        
        # Log slow requests (potential DoS)
        if duration > 5.0:
            logger.warning(f"Slow request: {request.path} took {duration:.2f}s from {request.remote_addr}")
        
        # Log failed authentication attempts
        if response.status_code == 401:
            logger.warning(f"Authentication failed: {request.path} from {request.remote_addr}")
        
        # Log access to sensitive endpoints
        if self.is_sensitive_endpoint() and response.status_code == 200:
            logger.info(f"Sensitive endpoint access: {request.path} from {request.remote_addr}")
    
    def rate_limit_handler(self, e):
        """Handle rate limit exceeded"""
        return jsonify({
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }), 429
    
    def forbidden_handler(self, e):
        """Handle forbidden access"""
        return jsonify({
            'error': 'Access forbidden',
            'message': 'Request blocked for security reasons.'
        }), 403


def require_api_key(f: Callable) -> Callable:
    """Decorator to require API key for certain endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        # Validate API key (implement your validation logic)
        if not validate_api_key(api_key):
            return jsonify({'error': 'Invalid API key'}), 401
        
        return f(*args, **kwargs)
    return decorated_function


def validate_api_key(api_key: str) -> bool:
    """Validate API key"""
    # TODO: Implement proper API key validation
    # This could check against database, hash comparison, etc.
    valid_keys = current_app.config.get('VALID_API_KEYS', [])
    return api_key in valid_keys


def admin_required(f: Callable) -> Callable:
    """Decorator to require admin privileges"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_jwt_extended import verify_jwt_in_request, get_jwt
        
        verify_jwt_in_request()
        claims = get_jwt()
        
        if not claims.get('is_admin', False):
            return jsonify({'error': 'Admin privileges required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function


def log_security_event(event_type: str, details: Dict[str, Any]):
    """Log security events for monitoring"""
    security_log = {
        'timestamp': datetime.utcnow().isoformat(),
        'event_type': event_type,
        'ip_address': request.remote_addr,
        'user_agent': request.headers.get('User-Agent'),
        'endpoint': request.endpoint,
        'details': details
    }
    
    # Log to file/database/external service
    logger.warning(f"Security Event: {json.dumps(security_log)}")