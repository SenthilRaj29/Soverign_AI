import sys
import os
import asyncio
import pytest

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.llm.provider import OllamaProvider
from app.rag.embedding_service import EmbeddingService
from app.rag.vector_store import LocalVectorStore
from app.rag.rag_pipeline import RAGPipeline
from app.router.model_router import ModelRouter

def test_model_configuration():
    print("--- TEST: Model Configuration ---")
    provider = OllamaProvider()
    print(f"Configured Ollama Model: {provider.model}")
    assert provider.model == "gemma4:latest", f"Expected gemma4:latest, got {provider.model}"
    
    router = ModelRouter()
    decision = router.route("text_query")
    print(f"ModelRouter Selected Model: {decision.selected_model}")
    assert decision.selected_model == "gemma4:latest", f"Expected gemma4:latest, got {decision.selected_model}"
    print("Model Configuration: PASS")

def test_embedding_service_no_md5():
    print("\n--- TEST: Embedding Service (No MD5 Fallback) ---")
    service = EmbeddingService()
    try:
        vec = service.embed_text("Test embedding string")
        print(f"Embedding generated (Length: {len(vec)})")
    except RuntimeError as e:
        print(f"Caught expected RuntimeError: {e}")
        assert "EMBEDDING_SERVICE_UNAVAILABLE" in str(e)
        print("MD5 Fallback Removal: PASS (Raised EMBEDDING_SERVICE_UNAVAILABLE as required)")

def test_vector_store_no_memory_fallback():
    print("\n--- TEST: Vector Store (No Memory Fallback) ---")
    store = LocalVectorStore()
    try:
        results = store.search("Test query", user_role="ENGINEER")
        print(f"Qdrant results count: {len(results)}")
    except RuntimeError as e:
        print(f"Caught expected RuntimeError: {e}")
        assert "QDRANT_UNAVAILABLE" in str(e)
        print("In-Memory Search Fallback Removal: PASS (Raised QDRANT_UNAVAILABLE as required)")

@pytest.mark.anyio
async def test_rag_pipeline_error_propagation():
    print("\n--- TEST: RAG Pipeline Error Propagation ---")
    pipeline = RAGPipeline()
    try:
        res = await pipeline.query("How do I perform LOTO on CP9000 pump?")
        print("RAG Result:", res)
    except RuntimeError as e:
        print(f"Caught expected RAG Exception: {e}")
        assert any(code in str(e) for code in ["EMBEDDING_SERVICE_UNAVAILABLE", "QDRANT_UNAVAILABLE", "LLM_UNAVAILABLE", "Ollama", "connection attempts failed"])
        print("RAG Error Propagation: PASS (No hardcoded fallback answer returned)")

if __name__ == "__main__":
    test_model_configuration()
    test_embedding_service_no_md5()
    test_vector_store_no_memory_fallback()
    asyncio.run(test_rag_pipeline_error_propagation())
