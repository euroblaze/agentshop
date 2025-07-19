import openai
from typing import Dict, Any, List, Optional
from .base_llm_provider import BaseLLMProvider, LLMProvider, LLMRequest, LLMResponse


class OpenAIProvider(BaseLLMProvider):
    """OpenAI API provider"""
    
    PRICING = {
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-32k": {"input": 0.06, "output": 0.12},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006}
    }
    
    def __init__(self, api_key: str, organization: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key=api_key, config=config)
        self.organization = organization
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            organization=organization
        )
    
    def _get_provider_type(self) -> LLMProvider:
        return LLMProvider.OPENAI
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API"""
        try:
            messages = [{"role": "user", "content": request.prompt}]
            
            if request.context and "system_prompt" in request.context:
                messages.insert(0, {"role": "system", "content": request.context["system_prompt"]})
            
            if request.context and "conversation_history" in request.context:
                messages = request.context["conversation_history"] + messages
            
            response = await self.client.chat.completions.create(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                top_p=request.top_p,
                stream=request.stream
            )
            
            if request.stream:
                content = ""
                async for chunk in response:
                    if chunk.choices[0].delta.content:
                        content += chunk.choices[0].delta.content
                tokens_used = len(content.split())
            else:
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
                    "organization": self.organization
                },
                cached=False
            )
        
        except Exception as e:
            raise Exception(f"OpenAI generation failed: {str(e)}")
    
    def validate_config(self) -> bool:
        """Validate OpenAI configuration"""
        return self.api_key is not None and len(self.api_key.strip()) > 0
    
    def get_available_models(self) -> List[str]:
        """Get list of available OpenAI models"""
        return [
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-4",
            "gpt-4-32k",
            "gpt-4-turbo",
            "gpt-4o",
            "gpt-4o-mini"
        ]
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for OpenAI request"""
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