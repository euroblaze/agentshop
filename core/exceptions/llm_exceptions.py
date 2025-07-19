#!/usr/bin/env python3
"""
LLM-specific Exceptions

Specialized exceptions for Large Language Model operations and provider interactions.
"""

from typing import Optional, Dict, Any
from .base_exceptions import ExternalServiceError, APIError


class LLMError(ExternalServiceError):
    """Base exception for LLM-related errors."""
    
    def __init__(self, 
                 message: str = "LLM Error",
                 provider: Optional[str] = None,
                 model: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            service_name=provider or "LLM Provider",
            **kwargs
        )
        self.error_code = "LLM_ERROR"
        self.provider = provider
        self.model = model
        
        self.details.update({
            'provider': provider,
            'model': model
        })


class LLMProviderError(LLMError):
    """Exception for general LLM provider errors."""
    
    def __init__(self, 
                 message: str = "LLM Provider Error",
                 provider_error_code: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "LLM_PROVIDER_ERROR"
        self.provider_error_code = provider_error_code
        
        if provider_error_code:
            self.details['provider_error_code'] = provider_error_code


class LLMAuthenticationError(LLMError):
    """Exception for LLM provider authentication failures."""
    
    def __init__(self, 
                 message: str = "LLM Provider Authentication Failed",
                 auth_type: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "LLM_AUTH_ERROR"
        self.status_code = 401
        self.auth_type = auth_type
        
        if auth_type:
            self.details['auth_type'] = auth_type


class LLMQuotaError(LLMError):
    """Exception for LLM provider quota or rate limit exceeded."""
    
    def __init__(self, 
                 message: str = "LLM Provider Quota Exceeded",
                 quota_type: Optional[str] = None,
                 limit: Optional[int] = None,
                 reset_time: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "LLM_QUOTA_ERROR"
        self.status_code = 429
        self.quota_type = quota_type
        self.limit = limit
        self.reset_time = reset_time
        
        self.details.update({
            'quota_type': quota_type,
            'limit': limit,
            'reset_time': reset_time
        })


class LLMTimeoutError(LLMError):
    """Exception for LLM request timeouts."""
    
    def __init__(self, 
                 message: str = "LLM Request Timeout",
                 timeout_duration: Optional[int] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "LLM_TIMEOUT_ERROR"
        self.status_code = 504
        self.timeout_duration = timeout_duration
        
        if timeout_duration:
            self.details['timeout_duration'] = timeout_duration


class LLMModelError(LLMError):
    """Exception for LLM model-related errors."""
    
    def __init__(self, 
                 message: str = "LLM Model Error",
                 model_error_type: Optional[str] = None,
                 available_models: Optional[list] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "LLM_MODEL_ERROR"
        self.model_error_type = model_error_type
        self.available_models = available_models or []
        
        self.details.update({
            'model_error_type': model_error_type,
            'available_models': self.available_models
        })


class LLMServiceError(LLMError):
    """Exception for general LLM service errors."""
    
    def __init__(self, 
                 message: str = "LLM Service Error",
                 service_status: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "LLM_SERVICE_ERROR"
        self.service_status = service_status
        
        if service_status:
            self.details['service_status'] = service_status


class LLMContentFilterError(LLMError):
    """Exception for content filtering violations."""
    
    def __init__(self, 
                 message: str = "Content Filter Violation",
                 filter_type: Optional[str] = None,
                 filtered_content: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "LLM_CONTENT_FILTER_ERROR"
        self.status_code = 400
        self.filter_type = filter_type
        self.filtered_content = filtered_content
        
        self.details.update({
            'filter_type': filter_type,
            'filtered_content': filtered_content
        })


class LLMConfigurationError(LLMError):
    """Exception for LLM configuration errors."""
    
    def __init__(self, 
                 message: str = "LLM Configuration Error",
                 config_parameter: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "LLM_CONFIG_ERROR"
        self.status_code = 500
        self.config_parameter = config_parameter
        
        if config_parameter:
            self.details['config_parameter'] = config_parameter


class LLMResponseError(LLMError):
    """Exception for invalid or malformed LLM responses."""
    
    def __init__(self, 
                 message: str = "Invalid LLM Response",
                 response_error_type: Optional[str] = None,
                 raw_response: Optional[str] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "LLM_RESPONSE_ERROR"
        self.response_error_type = response_error_type
        self.raw_response = raw_response
        
        self.details.update({
            'response_error_type': response_error_type,
            'raw_response': raw_response
        })


class LLMTokenLimitError(LLMError):
    """Exception for token limit exceeded errors."""
    
    def __init__(self, 
                 message: str = "Token Limit Exceeded",
                 token_limit: Optional[int] = None,
                 token_count: Optional[int] = None,
                 **kwargs):
        super().__init__(
            message=message,
            **kwargs
        )
        self.error_code = "LLM_TOKEN_LIMIT_ERROR"
        self.status_code = 400
        self.token_limit = token_limit
        self.token_count = token_count
        
        self.details.update({
            'token_limit': token_limit,
            'token_count': token_count
        })


# Provider-specific exceptions

class OpenAIError(LLMError):
    """Exception for OpenAI-specific errors."""
    
    def __init__(self, message: str = "OpenAI Error", **kwargs):
        super().__init__(
            message=message,
            provider="OpenAI",
            **kwargs
        )
        self.error_code = "OPENAI_ERROR"


class ClaudeError(LLMError):
    """Exception for Anthropic Claude-specific errors."""
    
    def __init__(self, message: str = "Claude Error", **kwargs):
        super().__init__(
            message=message,
            provider="Anthropic",
            **kwargs
        )
        self.error_code = "CLAUDE_ERROR"


class GroqError(LLMError):
    """Exception for Groq-specific errors."""
    
    def __init__(self, message: str = "Groq Error", **kwargs):
        super().__init__(
            message=message,
            provider="Groq",
            **kwargs
        )
        self.error_code = "GROQ_ERROR"


class OllamaError(LLMError):
    """Exception for Ollama-specific errors."""
    
    def __init__(self, message: str = "Ollama Error", **kwargs):
        super().__init__(
            message=message,
            provider="Ollama",
            **kwargs
        )
        self.error_code = "OLLAMA_ERROR"


class PerplexityError(LLMError):
    """Exception for Perplexity-specific errors."""
    
    def __init__(self, message: str = "Perplexity Error", **kwargs):
        super().__init__(
            message=message,
            provider="Perplexity",
            **kwargs
        )
        self.error_code = "PERPLEXITY_ERROR"


# Utility functions for LLM error handling

def categorize_llm_error(error_message: str, provider: Optional[str] = None) -> str:
    """
    Categorize an LLM error based on the error message.
    
    Args:
        error_message: The error message from the LLM provider
        provider: The LLM provider name
        
    Returns:
        Error category string
    """
    error_lower = error_message.lower()
    
    if any(keyword in error_lower for keyword in ['api key', 'authentication', 'unauthorized']):
        return 'authentication'
    elif any(keyword in error_lower for keyword in ['quota', 'limit', 'rate']):
        return 'quota'
    elif any(keyword in error_lower for keyword in ['timeout', 'timed out']):
        return 'timeout'
    elif any(keyword in error_lower for keyword in ['model', 'not found', 'unavailable']):
        return 'model'
    elif any(keyword in error_lower for keyword in ['content', 'filter', 'violation']):
        return 'content_filter'
    elif any(keyword in error_lower for keyword in ['token', 'length', 'exceed']):
        return 'token_limit'
    else:
        return 'service'


def create_llm_error_from_response(response: Dict[str, Any], 
                                  provider: Optional[str] = None,
                                  model: Optional[str] = None) -> LLMError:
    """
    Create an appropriate LLM error from a provider response.
    
    Args:
        response: Response from LLM provider
        provider: Provider name
        model: Model name
        
    Returns:
        Appropriate LLM error instance
    """
    error_message = response.get('error', {}).get('message', 'Unknown LLM error')
    error_code = response.get('error', {}).get('code')
    
    category = categorize_llm_error(error_message, provider)
    
    if category == 'authentication':
        return LLMAuthenticationError(
            message=error_message,
            provider=provider,
            model=model,
            provider_error_code=error_code
        )
    elif category == 'quota':
        return LLMQuotaError(
            message=error_message,
            provider=provider,
            model=model,
            provider_error_code=error_code
        )
    elif category == 'timeout':
        return LLMTimeoutError(
            message=error_message,
            provider=provider,
            model=model
        )
    elif category == 'model':
        return LLMModelError(
            message=error_message,
            provider=provider,
            model=model,
            model_error_type=error_code
        )
    elif category == 'content_filter':
        return LLMContentFilterError(
            message=error_message,
            provider=provider,
            model=model,
            filter_type=error_code
        )
    elif category == 'token_limit':
        return LLMTokenLimitError(
            message=error_message,
            provider=provider,
            model=model
        )
    else:
        return LLMServiceError(
            message=error_message,
            provider=provider,
            model=model,
            service_error_code=error_code
        )