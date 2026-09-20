import time
import httpx
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

class ChatMessage(BaseModel):
    role: str # "system", "user", "assistant"
    content: str
    images: Optional[List[str]] = None # base64 encoded images for multimodal

class LLMResponse(BaseModel):
    content: str
    model: str
    latency_ms: float
    prompt_tokens: Optional[int] = 0
    completion_tokens: Optional[int] = 0

class LLMProvider(ABC):
    @abstractmethod
    async def chat(self, messages: List[ChatMessage], temperature: float = 0.2, max_tokens: int = 2048) -> LLMResponse:
        pass

    @abstractmethod
    async def health(self) -> Dict[str, Any]:
        pass

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "gemma4:latest", timeout: float = 120.0):
        self.base_url = base_url.rstrip('/')
        self.model = model
        self.timeout = timeout

    async def chat(self, messages: List[ChatMessage], temperature: float = 0.2, max_tokens: int = 2048) -> LLMResponse:
        start_time = time.time()
        payload = {
            "model": self.model,
            "messages": [msg.model_dump(exclude_none=True) for msg in messages],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                data = response.json()
                latency = round((time.time() - start_time) * 1000, 2)
                
                content = data.get("message", {}).get("content", "")
                prompt_tokens = data.get("prompt_eval_count", 0)
                completion_tokens = data.get("eval_count", 0)
                
                return LLMResponse(
                    content=content,
                    model=self.model,
                    latency_ms=latency,
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens
                )
            except Exception as e:
                raise RuntimeError(f"Ollama local inference error: {str(e)}")

    async def health(self) -> Dict[str, Any]:
        start_time = time.time()
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                response = await client.get(f"{self.base_url}/api/tags")
                latency = round((time.time() - start_time) * 1000, 2)
                if response.status_code == 200:
                    models = [m.get("name") for m in response.json().get("models", [])]
                    model_available = any(self.model in m or m.startswith(self.model.split(':')[0]) for m in models)
                    return {
                        "status": "healthy" if model_available else "degraded",
                        "provider": "ollama",
                        "endpoint": self.base_url,
                        "configured_model": self.model,
                        "model_available": model_available,
                        "available_models": models,
                        "latency_ms": latency
                    }
                return {"status": "unhealthy", "error": f"HTTP {response.status_code}"}
            except Exception as e:
                return {
                    "status": "unhealthy",
                    "provider": "ollama",
                    "endpoint": self.base_url,
                    "error": str(e),
                    "model_available": False
                }
