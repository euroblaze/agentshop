from groq import AsyncGroq
from typing import Dict, Any, List, Optional
from .base_llm_provider import BaseLLMProvider, LLMProvider, LLMRequest, LLMResponse


class GroqProvider(BaseLLMProvider):
    """Groq API provider for fast LLM inference"""
    
    PRICING = {
        # Groq pricing per 1M tokens (as of 2024)
        "llama2-70b-4096": {"input": 0.0007, "output": 0.0008},
        "llama3-8b-8192": {"input": 0.0005, "output": 0.0008},
        "llama3-70b-8192": {"input": 0.0007, "output": 0.0008},
        "mixtral-8x7b-32768": {"input": 0.0005, "output": 0.0008},
        "gemma-7b-it": {"input": 0.0001, "output": 0.0002},
        "gemma2-9b-it": {"input": 0.0002, "output": 0.0002},
        "llama-3.1-8b-instant": {"input": 0.0005, "output": 0.0008},
        "llama-3.1-70b-versatile": {"input": 0.0007, "output": 0.0008},
        "llama-3.2-1b-preview": {"input": 0.0004, "output": 0.0004},
        "llama-3.2-3b-preview": {"input": 0.0006, "output": 0.0006},
        "llama-3.2-11b-vision-preview": {"input": 0.0018, "output": 0.0018},
        "llama-3.2-90b-vision-preview": {"input": 0.009, "output": 0.009}
    }
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key=api_key, config=config)
        self.client = AsyncGroq(api_key=api_key)
    
    def _get_provider_type(self) -> LLMProvider:
        return LLMProvider.GROQ
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Groq API"""
        try:
            messages = [{"role": "user", "content": request.prompt}]
            
            if request.context and "system_prompt" in request.context:
                messages.insert(0, {"role": "system", "content": request.context["system_prompt"]})
            
            if request.context and "conversation_history" in request.context:
                messages = request.context["conversation_history"] + messages
            
            kwargs = {
                "model": request.model,
                "messages": messages,
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
                "top_p": request.top_p,
                "stream": request.stream
            }
            
            if request.stream:
                response = await self.client.chat.completions.create(stream=True, **kwargs)
                content = ""
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                tokens_used = len(content.split())  # Approximate for streaming
            else:
                response = await self.client.chat.completions.create(**kwargs)
                content = response.choices[0].message.content
                tokens_used = response.usage.total_tokens if response.usage else len(content.split())
            
            cost = self._calculate_cost(request.model, tokens_used)
            
            return LLMResponse(
                content=content,
                provider=self.provider,
                model=request.model,
                tokens_used=tokens_used,
                cost=cost,
                metadata={
                    "finish_reason": response.choices[0].finish_reason if not request.stream else None,
                    "model": response.model if not request.stream else request.model,
                    "created": response.created if not request.stream else None
                },
                cached=False
            )
        
        except Exception as e:
            raise Exception(f"Groq generation failed: {str(e)}")
    
    def validate_config(self) -> bool:
        """Validate Groq configuration"""
        return self.api_key is not None and len(self.api_key.strip()) > 0
    
    def get_available_models(self) -> List[str]:
        """Get list of available Groq models"""
        return [
            "llama2-70b-4096",
            "llama3-8b-8192", 
            "llama3-70b-8192",
            "mixtral-8x7b-32768",
            "gemma-7b-it",
            "gemma2-9b-it",
            "llama-3.1-8b-instant",
            "llama-3.1-70b-versatile",
            "llama-3.2-1b-preview",
            "llama-3.2-3b-preview",
            "llama-3.2-11b-vision-preview",
            "llama-3.2-90b-vision-preview"
        ]
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for Groq request"""
        estimated_tokens = len(request.prompt.split()) * 1.3  # Rough estimation
        return self._calculate_cost(request.model, estimated_tokens)
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost based on model and token usage"""
        if model in self.PRICING:
            # Simplified: assume 50/50 input/output split
            input_tokens = tokens * 0.5
            output_tokens = tokens * 0.5
            
            pricing = self.PRICING[model]
            cost = (input_tokens * pricing["input"] / 1000000) + (output_tokens * pricing["output"] / 1000000)
            return round(cost, 8)  # Higher precision for very low costs
        
        return 0.0