from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from app.llm.provider import OllamaProvider, ChatMessage, LLMResponse

router = APIRouter(prefix="/api/llm", tags=["LLM"])

# Instantiate local Ollama provider
ollama_provider = OllamaProvider()

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 2048

@router.post("/chat", response_model=LLMResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        response = await ollama_provider.chat(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_endpoint():
    return await ollama_provider.health()
