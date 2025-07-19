from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class LLMProvider(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    CLAUDE = "claude"
    PERPLEXITY = "perplexity"


@dataclass
class LLMRequest:
    prompt: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 1.0
    stream: bool = False
    context: Optional[Dict[str, Any]] = None


@dataclass
class LLMResponse:
    content: str
    provider: LLMProvider
    model: str
    tokens_used: int
    cost: float = 0.0
    metadata: Optional[Dict[str, Any]] = None
    cached: bool = False


class BaseLLMProvider(ABC):
    """Abstract base class for all LLM providers"""
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        self.api_key = api_key
        self.config = config or {}
        self.provider = self._get_provider_type()
    
    @abstractmethod
    def _get_provider_type(self) -> LLMProvider:
        """Return the provider type enum"""
        pass
    
    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate a response from the LLM"""
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the provider configuration"""
        pass
    
    @abstractmethod
    def get_available_models(self) -> List[str]:
        """Get list of available models for this provider"""
        pass
    
    @abstractmethod
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate the cost for a request"""
        pass
    
    def _prepare_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Prepare request data for the specific provider"""
        return {
            "prompt": request.prompt,
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": request.stream
        }
    
    def _process_response(self, raw_response: Any, request: LLMRequest) -> LLMResponse:
        """Process raw response into standardized format"""
        return LLMResponse(
            content="",
            provider=self.provider,
            model=request.model,
            tokens_used=0,
            cost=0.0,
            metadata=None,
            cached=False
        )