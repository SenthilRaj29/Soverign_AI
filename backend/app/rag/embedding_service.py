from typing import List

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None

class EmbeddingService:
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        if SentenceTransformer is not None:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception:
                self.model = None
        else:
            self.model = None
        self.vector_dim = 384

    def embed_text(self, text: str) -> List[float]:
        if self.model:
            try:
                return self.model.encode(text).tolist()
            except Exception as e:
                raise RuntimeError(f"EMBEDDING_SERVICE_UNAVAILABLE: Failed to generate embedding with BAAI/bge-small-en-v1.5: {str(e)}")
        raise RuntimeError("EMBEDDING_SERVICE_UNAVAILABLE: BAAI/bge-small-en-v1.5 embedding model could not be loaded.")

    def embed_documents(self, documents: List[str]) -> List[List[float]]:
        return [self.embed_text(doc) for doc in documents]

    def embed_query(self, query: str) -> List[float]:
        return self.embed_text(query)
