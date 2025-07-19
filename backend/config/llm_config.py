import os
from typing import Dict, Any, Optional
from dataclasses import dataclass, asdict
from ..services.llm import LLMProvider


@dataclass
class ProviderConfig:
    """Configuration for an LLM provider"""
    enabled: bool = False
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    organization: Optional[str] = None
    default_model: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    rate_limit_rpm: int = 60  # requests per minute
    cost_limit_daily: float = 10.0  # dollars per day


@dataclass
class LLMConfig:
    """Main LLM configuration"""
    default_provider: str = "openai"
    cache_ttl: int = 3600  # 1 hour
    enable_caching: bool = True
    enable_rate_limiting: bool = True
    log_requests: bool = True
    providers: Dict[str, ProviderConfig] = None
    
    def __post_init__(self):
        if self.providers is None:
            self.providers = {}


class LLMConfigManager:
    """Manager for LLM configuration"""
    
    def __init__(self):
        self.config = LLMConfig()
        self.load_from_environment()
    
    def load_from_environment(self):
        """Load configuration from environment variables"""
        
        # General settings
        self.config.default_provider = os.getenv('LLM_DEFAULT_PROVIDER', 'openai')
        self.config.cache_ttl = int(os.getenv('LLM_CACHE_TTL', '3600'))
        self.config.enable_caching = os.getenv('LLM_ENABLE_CACHING', 'true').lower() == 'true'
        self.config.enable_rate_limiting = os.getenv('LLM_ENABLE_RATE_LIMITING', 'true').lower() == 'true'
        self.config.log_requests = os.getenv('LLM_LOG_REQUESTS', 'true').lower() == 'true'
        
        # Load provider configurations
        for provider in LLMProvider:
            provider_name = provider.value
            self.config.providers[provider_name] = self._load_provider_config(provider_name)
    
    def _load_provider_config(self, provider_name: str) -> ProviderConfig:
        """Load configuration for a specific provider"""
        prefix = f"LLM_{provider_name.upper()}_"
        
        config = ProviderConfig()
        config.enabled = os.getenv(f"{prefix}ENABLED", 'false').lower() == 'true'
        config.api_key = os.getenv(f"{prefix}API_KEY")
        config.base_url = os.getenv(f"{prefix}BASE_URL")
        config.organization = os.getenv(f"{prefix}ORGANIZATION")
        config.default_model = os.getenv(f"{prefix}DEFAULT_MODEL")
        config.max_tokens = int(os.getenv(f"{prefix}MAX_TOKENS", '1000'))
        config.temperature = float(os.getenv(f"{prefix}TEMPERATURE", '0.7'))
        config.rate_limit_rpm = int(os.getenv(f"{prefix}RATE_LIMIT_RPM", '60'))
        config.cost_limit_daily = float(os.getenv(f"{prefix}COST_LIMIT_DAILY", '10.0'))
        
        return config
    
    def get_provider_config(self, provider_name: str) -> Optional[ProviderConfig]:
        """Get configuration for a specific provider"""
        return self.config.providers.get(provider_name)
    
    def is_provider_enabled(self, provider_name: str) -> bool:
        """Check if a provider is enabled"""
        config = self.get_provider_config(provider_name)
        return config is not None and config.enabled
    
    def get_enabled_providers(self) -> list[str]:
        """Get list of enabled provider names"""
        return [
            name for name, config in self.config.providers.items()
            if config.enabled
        ]
    
    def update_provider_config(self, provider_name: str, **kwargs):
        """Update configuration for a provider"""
        if provider_name not in self.config.providers:
            self.config.providers[provider_name] = ProviderConfig()
        
        config = self.config.providers[provider_name]
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    def enable_provider(self, provider_name: str, api_key: str, **kwargs):
        """Enable a provider with API key"""
        self.update_provider_config(
            provider_name,
            enabled=True,
            api_key=api_key,
            **kwargs
        )
    
    def disable_provider(self, provider_name: str):
        """Disable a provider"""
        self.update_provider_config(provider_name, enabled=False)
    
    def validate_config(self) -> Dict[str, Any]:
        """Validate current configuration and return issues"""
        issues = []
        
        # Check if at least one provider is enabled
        enabled_providers = self.get_enabled_providers()
        if not enabled_providers:
            issues.append("No LLM providers are enabled")
        
        # Validate each enabled provider
        for provider_name in enabled_providers:
            config = self.get_provider_config(provider_name)
            
            # Check API key for providers that need it
            if provider_name != 'ollama' and not config.api_key:
                issues.append(f"Provider {provider_name} is enabled but missing API key")
            
            # Check base URL for Ollama
            if provider_name == 'ollama' and not config.base_url:
                issues.append("Ollama provider is enabled but missing base URL")
        
        # Check default provider
        if self.config.default_provider not in enabled_providers:
            issues.append(f"Default provider '{self.config.default_provider}' is not enabled")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "enabled_providers": enabled_providers
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            "default_provider": self.config.default_provider,
            "cache_ttl": self.config.cache_ttl,
            "enable_caching": self.config.enable_caching,
            "enable_rate_limiting": self.config.enable_rate_limiting,
            "log_requests": self.config.log_requests,
            "providers": {
                name: asdict(config) for name, config in self.config.providers.items()
            }
        }
    
    def get_safe_config(self) -> Dict[str, Any]:
        """Get configuration without sensitive data (API keys)"""
        safe_config = self.to_dict()
        
        # Remove API keys from the safe config
        for provider_config in safe_config["providers"].values():
            if provider_config.get("api_key"):
                provider_config["api_key"] = "***hidden***"
        
        return safe_config


# Global configuration manager instance
config_manager = LLMConfigManager()