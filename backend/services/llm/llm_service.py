import asyncio
from typing import Dict, Any, Optional, List
from .base_llm_provider import BaseLLMProvider, LLMRequest, LLMResponse, LLMProvider
from .llm_factory import LLMFactory
from .llm_cache import LLMCache


class LLMService:
    """High-level service for orchestrating multiple LLM providers"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.providers: Dict[LLMProvider, BaseLLMProvider] = {}
        self.cache = LLMCache()
        self.default_provider = None
    
    def register_provider(
        self,
        provider_type: LLMProvider,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        set_as_default: bool = False
    ):
        """Register an LLM provider"""
        provider = LLMFactory.create_provider(provider_type, api_key, config)
        self.providers[provider_type] = provider
        
        if set_as_default or not self.default_provider:
            self.default_provider = provider_type
    
    async def generate(
        self,
        prompt: str,
        provider: Optional[LLMProvider] = None,
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate a response using the specified or default provider"""
        
        # Use default provider if none specified
        if not provider:
            if not self.default_provider:
                raise ValueError("No provider specified and no default provider set")
            provider = self.default_provider
        
        # Check if provider is registered
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} is not registered")
        
        provider_instance = self.providers[provider]
        
        # Set default model if none specified
        if not model:
            available_models = provider_instance.get_available_models()
            if available_models:
                model = available_models[0]
            else:
                raise ValueError(f"No models available for provider {provider}")
        
        # Create request
        request = LLMRequest(
            prompt=prompt,
            model=model,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000),
            top_p=kwargs.get('top_p', 1.0),
            stream=kwargs.get('stream', False),
            context=kwargs.get('context')
        )
        
        # Check cache first
        cache_key = self.cache.generate_cache_key(request)
        cached_response = await self.cache.get(cache_key)
        if cached_response:
            cached_response.cached = True
            return cached_response
        
        # Generate response
        response = await provider_instance.generate(request)
        
        # Cache the response
        await self.cache.set(cache_key, response)
        
        return response
    
    async def generate_with_fallback(
        self,
        prompt: str,
        providers: List[LLMProvider],
        model: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """Generate with fallback to other providers if the first fails"""
        
        last_error = None
        
        for provider in providers:
            try:
                return await self.generate(prompt, provider, model, **kwargs)
            except Exception as e:
                last_error = e
                continue
        
        raise Exception(f"All providers failed. Last error: {last_error}")
    
    async def compare_providers(
        self,
        prompt: str,
        providers: List[LLMProvider],
        model: Optional[str] = None,
        **kwargs
    ) -> Dict[LLMProvider, LLMResponse]:
        """Generate responses from multiple providers for comparison"""
        
        tasks = []
        for provider in providers:
            if provider in self.providers:
                task = self.generate(prompt, provider, model, **kwargs)
                tasks.append((provider, task))
        
        results = {}
        for provider, task in tasks:
            try:
                results[provider] = await task
            except Exception as e:
                results[provider] = Exception(f"Provider {provider} failed: {str(e)}")
        
        return results
    
    def estimate_cost(
        self,
        prompt: str,
        provider: LLMProvider,
        model: Optional[str] = None,
        **kwargs
    ) -> float:
        """Estimate the cost for a request"""
        
        if provider not in self.providers:
            return 0.0
        
        provider_instance = self.providers[provider]
        
        if not model:
            available_models = provider_instance.get_available_models()
            model = available_models[0] if available_models else ""
        
        request = LLMRequest(
            prompt=prompt,
            model=model,
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 1000),
            top_p=kwargs.get('top_p', 1.0),
            stream=kwargs.get('stream', False),
            context=kwargs.get('context')
        )
        
        return provider_instance.estimate_cost(request)
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of registered providers"""
        return list(self.providers.keys())
    
    def get_available_models(self, provider: LLMProvider) -> List[str]:
        """Get available models for a specific provider"""
        if provider not in self.providers:
            return []
        return self.providers[provider].get_available_models()
    
    async def health_check(self) -> Dict[LLMProvider, bool]:
        """Check health of all registered providers"""
        results = {}
        
        for provider_type, provider in self.providers.items():
            try:
                # Simple test generation
                test_request = LLMRequest(
                    prompt="Hello",
                    model=provider.get_available_models()[0] if provider.get_available_models() else "default",
                    max_tokens=5
                )
                await provider.generate(test_request)
                results[provider_type] = True
            except:
                results[provider_type] = False
        
        return results
    
    async def close(self):
        """Close all provider connections"""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()