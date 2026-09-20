import logging
from typing import List, Dict, Any, Optional
from app.rag.vector_store import LocalVectorStore
from app.llm.provider import OllamaProvider, ChatMessage

logger = logging.getLogger("RAGPipeline")

class RAGPipeline:
    def __init__(self, vector_store: Optional[LocalVectorStore] = None, llm_provider: Optional[OllamaProvider] = None):
        self.vector_store = vector_store or LocalVectorStore()
        self.llm_provider = llm_provider or OllamaProvider()

    async def query(self, query_text: str, user_role: str = "ENGINEER", top_k: int = 4) -> Dict[str, Any]:
        logger.info(f"[INFO] Query received: '{query_text[:60]}...' (User Role: {user_role})")
        
        # 1. Retrieve grounded documents from local Qdrant filtered by user RBAC role
        chunks = self.vector_store.search(query=query_text, user_role=user_role, top_k=top_k)
        logger.info(f"[INFO] Qdrant search executed successfully. Retrieved {len(chunks)} chunks.")

        if not chunks:
            return {
                "answer": "Sufficient evidence was not found in the authorized organizational knowledge base.",
                "sources": [],
                "grounded": False,
                "model_used": self.llm_provider.model,
                "latency_ms": 0.0
            }

        # 2. Build explicit context block
        context_str = "RELEVANT ORGANIZATIONAL KNOWLEDGE CONTEXT:\n"
        sources = []
        for idx, chk in enumerate(chunks, 1):
            src_label = f"[{idx}] {chk['filename']} (Page {chk['page_number']}, Section: {chk['section']})"
            context_str += f"\n--- Source {src_label} ---\n{chk['content']}\n"
            sources.append({
                "source_num": idx,
                "filename": chk['filename'],
                "page_number": chk['page_number'],
                "section": chk['section'],
                "classification": chk['classification']
            })

        # 3. Formulate strict system policy preventing hallucination
        system_prompt = (
            "You are an AI Assistant for confidential enterprise operations.\n"
            "STRICT RULES:\n"
            "1. Answer the question using ONLY the provided organizational context.\n"
            "2. Always cite sources explicitly using [Filename, Page X].\n"
            "3. If sufficient information is not provided in the context, explicitly state: "
            "'Sufficient evidence was not found in the authorized organizational knowledge base.'\n"
            "4. Do NOT hallucinate or assume facts not stated in the context."
        )

        user_prompt = f"{context_str}\n\nUSER QUESTION: {query_text}\n\nANSWER:"

        messages = [
            ChatMessage(role="system", content=system_prompt),
            ChatMessage(role="user", content=user_prompt)
        ]

        logger.info(f"[INFO] Context constructed ({len(context_str)} chars). Dispatching request to Ollama ({self.llm_provider.model})...")

        try:
            response = await self.llm_provider.chat(messages, temperature=0.1)
            answer_text = response.content
            
            if not answer_text or not answer_text.strip():
                raise RuntimeError(f"LLM_UNAVAILABLE: Local Ollama model '{self.llm_provider.model}' returned an empty completion response.")

            logger.info(f"[INFO] Gemma response received successfully ({response.latency_ms}ms).")

            return {
                "answer": answer_text,
                "sources": sources,
                "grounded": True,
                "model_used": getattr(response, "model", self.llm_provider.model),
                "latency_ms": getattr(response, "latency_ms", 0.0)
            }
        except RuntimeError as re:
            logger.error(f"[ERROR] LLM generation failed: {str(re)}")
            raise re
        except Exception as e:
            logger.error(f"[ERROR] LLM generation failed: {str(e)}")
            raise RuntimeError(f"LLM_UNAVAILABLE: Local Ollama model '{self.llm_provider.model}' inference failed: {str(e)}")

