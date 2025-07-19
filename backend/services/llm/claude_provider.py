import anthropic
from typing import Dict, Any, List, Optional
from .base_llm_provider import BaseLLMProvider, LLMProvider, LLMRequest, LLMResponse


class ClaudeProvider(BaseLLMProvider):
    """Anthropic Claude API provider"""
    
    PRICING = {
        "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
        "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
        "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
        "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
        "claude-3-5-haiku-20241022": {"input": 0.001, "output": 0.005}
    }
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key=api_key, config=config)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    def _get_provider_type(self) -> LLMProvider:
        return LLMProvider.CLAUDE
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Claude API"""
        try:
            messages = [{"role": "user", "content": request.prompt}]
            
            system_prompt = None
            if request.context and "system_prompt" in request.context:
                system_prompt = request.context["system_prompt"]
            
            if request.context and "conversation_history" in request.context:
                messages = request.context["conversation_history"] + messages
            
            kwargs = {
                "model": request.model,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                "top_p": request.top_p,
                "messages": messages
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            if request.stream:
                response = await self.client.messages.create(stream=True, **kwargs)
                content = ""
                async for chunk in response:
                    if chunk.type == "content_block_delta":
                        content += chunk.delta.text
                tokens_used = len(content.split())
            else:
                response = await self.client.messages.create(**kwargs)
                content = response.content[0].text if response.content else ""
                tokens_used = response.usage.input_tokens + response.usage.output_tokens if response.usage else len(content.split())
            
            cost = self._calculate_cost(request.model, tokens_used)
            
            return LLMResponse(
                content=content,
                provider=self.provider,
                model=request.model,
                tokens_used=tokens_used,
                cost=cost,
                metadata={
                    "stop_reason": response.stop_reason if not request.stream else None,
                    "stop_sequence": response.stop_sequence if not request.stream else None
                },
                cached=False
            )
        
        except Exception as e:
            raise Exception(f"Claude generation failed: {str(e)}")
    
    def validate_config(self) -> bool:
        """Validate Claude configuration"""
        return self.api_key is not None and len(self.api_key.strip()) > 0
    
    def get_available_models(self) -> List[str]:
        """Get list of available Claude models"""
        return [
            "claude-3-haiku-20240307",
            "claude-3-sonnet-20240229",
            "claude-3-opus-20240229",
            "claude-3-5-sonnet-20241022",
            "claude-3-5-haiku-20241022"
        ]
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for Claude request"""
        estimated_tokens = len(request.prompt.split()) * 1.3  # Rough estimation
        return self._calculate_cost(request.model, estimated_tokens)
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost based on model and token usage"""
        if model in self.PRICING:
            # Simplified: assume 50/50 input/output split
            input_tokens = tokens * 0.5
            output_tokens = tokens * 0.5
            
            pricing = self.PRICING[model]
            cost = (input_tokens * pricing["input"] / 1000) + (output_tokens * pricing["output"] / 1000)
            return round(cost, 6)
        
        return 0.0