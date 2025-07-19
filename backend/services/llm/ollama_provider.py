import aiohttp
import json
from typing import Dict, Any, List
from .base_llm_provider import BaseLLMProvider, LLMProvider, LLMRequest, LLMResponse


class OllamaProvider(BaseLLMProvider):
    """Ollama API provider for local LLM inference"""
    
    def __init__(self, base_url: str = "http://localhost:11434", config: Optional[Dict[str, Any]] = None):
        super().__init__(api_key=None, config=config)
        self.base_url = base_url.rstrip('/')
        self.session = None
    
    def _get_provider_type(self) -> LLMProvider:
        return LLMProvider.OLLAMA
    
    async def _get_session(self):
        if not self.session:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Ollama API"""
        session = await self._get_session()
        
        payload = {
            "model": request.model,
            "prompt": request.prompt,
            "stream": request.stream,
            "options": {
                "temperature": request.temperature,
                "num_predict": request.max_tokens,
                "top_p": request.top_p
            }
        }
        
        try:
            async with session.post(f"{self.base_url}/api/generate", json=payload) as response:
                if response.status != 200:
                    raise Exception(f"Ollama API error: {response.status}")
                
                if request.stream:
                    content = ""
                    async for line in response.content:
                        if line:
                            data = json.loads(line.decode())
                            if 'response' in data:
                                content += data['response']
                            if data.get('done', False):
                                break
                else:
                    data = await response.json()
                    content = data.get('response', '')
                
                return LLMResponse(
                    content=content,
                    provider=self.provider,
                    model=request.model,
                    tokens_used=len(content.split()),  # Approximate token count
                    cost=0.0,  # Ollama is free for local use
                    metadata={"base_url": self.base_url},
                    cached=False
                )
        
        except Exception as e:
            raise Exception(f"Ollama generation failed: {str(e)}")
    
    def validate_config(self) -> bool:
        """Validate Ollama configuration"""
        return self.base_url is not None
    
    async def get_available_models(self) -> List[str]:
        """Get list of available models from Ollama"""
        session = await self._get_session()
        
        try:
            async with session.get(f"{self.base_url}/api/tags") as response:
                if response.status == 200:
                    data = await response.json()
                    return [model['name'] for model in data.get('models', [])]
                return []
        except:
            return []
    
    def estimate_cost(self, request: LLMRequest) -> float:
        """Ollama is free for local use"""
        return 0.0
    
    async def close(self):
        """Close the HTTP session"""
        if self.session:
            await self.session.close()
            self.session = None