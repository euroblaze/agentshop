import aiohttp
import json
from typing import Dict, Any, List, Optional
from .base_llm_provider import BaseLLMProvider, LLMProvider, LLMRequest, LLMResponse


class PerplexityProvider(BaseLLMProvider):
    """Perplexity API provider for search-augmented generation"""
    
    PRICING = {
        "llama-3.1-sonar-small-128k-online": {"input": 0.0002, "output": 0.0002},
        "llama-3.1-sonar-large-128k-online": {"input": 0.001, "output": 0.001},
        "llama-3.1-sonar-huge-128k-online": {"input": 0.005, "output": 0.005}
    }
    
    def __init__(self, api_key: str, config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key=api_key, config=config)
        self.base_url = "https://api.perplexity.ai"
        self.session = None
    
    def _get_provider_type(self) -> LLMProvider:
        return LLMProvider.PERPLEXITY
    
    async def _get_session(self):
        if not self.session:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            self.session = aiohttp.ClientSession(headers=headers)
        return self.session
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Perplexity API"""
        session = await self._get_session()
        
        messages = [{"role": "user", "content": request.prompt}]
        
        if request.context and "system_prompt" in request.context:
            messages.insert(0, {"role": "system", "content": request.context["system_prompt"]})
        
        if request.context and "conversation_history" in request.context:
            messages = request.context["conversation_history"] + messages
        
        payload = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            "top_p": request.top_p,
            "stream": request.stream
        }
        
        # Add search-specific parameters
        if request.context:
            if "search_domain_filter" in request.context:
                payload["search_domain_filter"] = request.context["search_domain_filter"]
            if "return_citations" in request.context:
                payload["return_citations"] = request.context["return_citations"]
            if "search_recency_filter" in request.context:
                payload["search_recency_filter"] = request.context["search_recency_filter"]
        
        try:
            async with session.post(f"{self.base_url}/chat/completions", json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"Perplexity API error: {response.status} - {error_text}")
                
                if request.stream:
                    content = ""
                    citations = []
                    async for line in response.content:
                        if line:
                            line_text = line.decode().strip()
                            if line_text.startswith("data: "):
                                data_str = line_text[6:]
                                if data_str != "[DONE]":
                                    data = json.loads(data_str)
                                    if data.get("choices") and data["choices"][0].get("delta", {}).get("content"):
                                        content += data["choices"][0]["delta"]["content"]
                                    if data.get("citations"):
                                        citations.extend(data["citations"])
                    
                    tokens_used = len(content.split())
                    metadata = {"citations": citations} if citations else None
                else:
                    data = await response.json()
                    content = data["choices"][0]["message"]["content"] if data.get("choices") else ""
                    tokens_used = data.get("usage", {}).get("total_tokens", len(content.split()))
                    
                    metadata = {}
                    if data.get("citations"):
                        metadata["citations"] = data["citations"]
                    if data["choices"][0].get("finish_reason"):
                        metadata["finish_reason"] = data["choices"][0]["finish_reason"]
                
                cost = self._calculate_cost(request.model, tokens_used)
                
                return LLMResponse(
                    content=content,
                    provider=self.provider,
                    model=request.model,
                    tokens_used=tokens_used,
                    cost=cost,
                    metadata=metadata,
                    cached=False
                )
        
        except Exception as e:
            raise Exception(f"Perplexity generation failed: {str(e)}")
    
    def validate_config(self) -> bool:
        """Validate Perplexity configuration"""
        return self.api_key is not None and len(self.api_key.strip()) > 0
    
    def get_available_models(self) -> List[str]:
        """Get list of available Perplexity models"""
        return [
            "llama-3.1-sonar-small-128k-online",
            "llama-3.1-sonar-large-128k-online",
            "llama-3.1-sonar-huge-128k-online",
            "llama-3.1-8b-instruct",
            "llama-3.1-70b-instruct"
        ]
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Estimate cost for Perplexity request"""
        estimated_tokens = len(request.prompt.split()) * 1.3  # Rough estimation
        return self._calculate_cost(request.model, estimated_tokens)
    
    def _calculate_cost(self, model: str, tokens: int) -> float:
        """Calculate cost based on model and token usage"""
        if model in self.PRICING:
            # For Perplexity, input and output pricing is the same
            pricing = self.PRICING[model]
            cost = tokens * pricing["input"] / 1000
            return round(cost, 6)
        
        return 0.0
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None