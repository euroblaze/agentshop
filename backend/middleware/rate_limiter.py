import time
from typing import Dict, Optional
from flask import request, jsonify
from functools import wraps


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        self.requests: Dict[str, list] = {}
    
    def is_allowed(self, key: str, limit: int, window: int) -> bool:
        """
        Check if request is allowed within rate limit
        
        Args:
            key: Unique identifier for the client/endpoint
            limit: Maximum number of requests allowed
            window: Time window in seconds
        
        Returns:
            True if request is allowed, False otherwise
        """
        current_time = time.time()
        
        if key not in self.requests:
            self.requests[key] = []
        
        # Remove old requests outside the window
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if current_time - req_time < window
        ]
        
        # Check if limit is exceeded
        if len(self.requests[key]) >= limit:
            return False
        
        # Add current request
        self.requests[key].append(current_time)
        return True
    
    def get_reset_time(self, key: str, window: int) -> Optional[float]:
        """Get the time when rate limit will reset for a key"""
        if key not in self.requests or not self.requests[key]:
            return None
        
        oldest_request = min(self.requests[key])
        return oldest_request + window


# Global rate limiter instance
rate_limiter = RateLimiter()


def rate_limit(requests_per_minute: int = 60, per_user: bool = True):
    """
    Rate limiting decorator
    
    Args:
        requests_per_minute: Number of requests allowed per minute
        per_user: If True, limit per IP address. If False, global limit
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine the key for rate limiting
            if per_user:
                key = f"{request.endpoint}:{request.remote_addr}"
            else:
                key = f"{request.endpoint}:global"
            
            # Check rate limit
            if not rate_limiter.is_allowed(key, requests_per_minute, 60):
                reset_time = rate_limiter.get_reset_time(key, 60)
                
                response = jsonify({
                    "success": False,
                    "data": None,
                    "message": "Rate limit exceeded. Please try again later.",
                    "errors": ["too_many_requests"]
                })
                response.status_code = 429
                
                if reset_time:
                    response.headers['X-RateLimit-Reset'] = str(int(reset_time))
                
                response.headers['X-RateLimit-Limit'] = str(requests_per_minute)
                return response
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def llm_rate_limit(requests_per_minute: int = 20):
    """Specific rate limiter for LLM endpoints with lower limits"""
    return rate_limit(requests_per_minute=requests_per_minute, per_user=True)