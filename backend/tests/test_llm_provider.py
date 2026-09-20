import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.llm.provider import OllamaProvider, ChatMessage, LLMResponse

@pytest.mark.asyncio
async def test_ollama_provider_health_mock():
    provider = OllamaProvider()
    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = AsyncMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "models": [{"name": "gemma3:latest"}]
        }
        mock_get.return_value = mock_resp
        
        health = await provider.health()
        assert health["status"] == "healthy"
        assert health["model_available"] is True
        assert health["configured_model"] == "gemma3:latest"

@pytest.mark.asyncio
async def test_ollama_provider_chat_mock():
    provider = OllamaProvider()
    with patch("httpx.AsyncClient.post") as mock_post:
        mock_resp = AsyncMock()
        mock_resp.raise_for_status = lambda: None
        mock_resp.json.return_value = {
            "message": {"content": "Sovereign AI test response"},
            "prompt_eval_count": 10,
            "eval_count": 15
        }
        mock_post.return_value = mock_resp
        
        messages = [ChatMessage(role="user", content="Hello")]
        response = await provider.chat(messages)
        
        assert response.content == "Sovereign AI test response"
        assert response.model == "gemma3:latest"
        assert response.prompt_tokens == 10
        assert response.completion_tokens == 15
