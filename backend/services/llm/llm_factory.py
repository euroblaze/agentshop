from typing import Dict, Any, Optional
from .base_llm_provider import BaseLLMProvider, LLMProvider
from .ollama_provider import OllamaProvider
from .openai_provider import OpenAIProvider
from .claude_provider import ClaudeProvider
from .perplexity_provider import PerplexityProvider


class LLMFactory:
    """Factory class for creating LLM provider instances"""
    
    @staticmethod
    def create_provider(
        provider_type: LLMProvider,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseLLMProvider:
        """Create an LLM provider instance based on the provider type"""
        
        if provider_type == LLMProvider.OLLAMA:
            base_url = config.get("base_url", "http://localhost:11434") if config else "http://localhost:11434"
            return OllamaProvider(base_url=base_url, config=config)
        
        elif provider_type == LLMProvider.OPENAI:
            if not api_key:
                raise ValueError("API key is required for OpenAI provider")
            organization = config.get("organization") if config else None
            return OpenAIProvider(api_key=api_key, organization=organization, config=config)
        
        elif provider_type == LLMProvider.CLAUDE:
            if not api_key:
                raise ValueError("API key is required for Claude provider")
            return ClaudeProvider(api_key=api_key, config=config)
        
        elif provider_type == LLMProvider.PERPLEXITY:
            if not api_key:
                raise ValueError("API key is required for Perplexity provider")
            return PerplexityProvider(api_key=api_key, config=config)
        
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    @staticmethod
    def create_from_string(
        provider_name: str,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ) -> BaseLLMProvider:
        """Create an LLM provider instance from a string name"""
        try:
            provider_type = LLMProvider(provider_name.lower())
            return LLMFactory.create_provider(provider_type, api_key, config)
        except ValueError:
            raise ValueError(f"Unknown provider: {provider_name}")
    
    @staticmethod
    def get_supported_providers() -> List[str]:
        """Get list of supported provider names"""
        return [provider.value for provider in LLMProvider]