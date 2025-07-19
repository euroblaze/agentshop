import hashlib
import json
import time
from typing import Optional, Dict, Any
from .base_llm_provider import LLMRequest, LLMResponse


class LLMCache:
    """Caching layer for LLM responses"""
    
    def __init__(self, ttl: int = 3600):  # 1 hour default TTL
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.ttl = ttl
    
    def generate_cache_key(self, request: LLMRequest) -> str:
        """Generate a cache key for an LLM request"""
        # Create a deterministic hash of the request parameters
        cache_data = {
            "prompt": request.prompt,
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "context": request.context
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(cache_string.encode()).hexdigest()
    
    async def get(self, cache_key: str) -> Optional[LLMResponse]:
        """Get a cached response"""
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            
            # Check if cache entry is still valid
            if time.time() - cache_entry["timestamp"] < self.ttl:
                return cache_entry["response"]
            else:
                # Remove expired entry
                del self.cache[cache_key]
        
        return None
    
    async def set(self, cache_key: str, response: LLMResponse):
        """Cache a response"""
        self.cache[cache_key] = {
            "response": response,
            "timestamp": time.time()
        }
    
    def clear_expired(self):
        """Remove expired cache entries"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self.cache.items()
            if current_time - entry["timestamp"] >= self.ttl
        ]
        
        for key in expired_keys:
            del self.cache[key]
    
    def clear_all(self):
        """Clear all cached entries"""
        self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        current_time = time.time()
        expired_count = sum(
            1 for entry in self.cache.values()
            if current_time - entry["timestamp"] >= self.ttl
        )
        
        return {
            "total_entries": len(self.cache),
            "valid_entries": len(self.cache) - expired_count,
            "expired_entries": expired_count,
            "ttl_seconds": self.ttl
        }