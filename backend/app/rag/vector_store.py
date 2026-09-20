import os
import uuid
from typing import List, Dict, Any, Optional
from app.services.ingestion import DocumentChunk
from app.rag.embedding_service import EmbeddingService

try:
    from qdrant_client import QdrantClient
    from qdrant_client.http import models as rest_models
except ImportError:
    QdrantClient = None
    rest_models = None

class LocalVectorStore:
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "sovereign_knowledge",
        embedding_service: Optional[EmbeddingService] = None
    ):
        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.embedding_service = embedding_service or EmbeddingService()
        self.memory_store: List[Dict[str, Any]] = []

        if QdrantClient is not None:
            try:
                self.client = QdrantClient(host=host, port=port, timeout=3.0)
                self.client.get_collections()
                self._ensure_collection()
            except Exception:
                try:
                    self.client = QdrantClient(path=os.path.abspath("qdrant_db"))
                    self._ensure_collection()
                except Exception:
                    self.client = None
        else:
            self.client = None

        # Always seed default organizational knowledge chunks into memory store
        self._seed_default_knowledge()

    def _seed_default_knowledge(self):
        default_docs = [
            DocumentChunk(
                chunk_id="loto_sop_01",
                filename="NOVA_Safety_SOP_LOTO.txt",
                file_type="txt",
                page_number=1,
                section="Emergency Shutdown Mandate",
                content="STANDARD OPERATING PROCEDURE: LOCKOUT/TAGOUT (LOTO) NOVA-SOP-2024-08\n"
                        "Section 1: General High-Voltage Electrical Isolation Protocols.\n"
                        "Section 2: EMERGENCY SHUTDOWN MANDATE: Immediate emergency shutdown is STRICTLY REQUIRED if pump operating temperature exceeds 85.0°C or vibration exceeds 4.5 mm/s RMS. "
                        "Operators must isolate high-voltage power breakers, attach physical safety padlocks, and tag equipment prior to maintenance.",
                department="SAFETY",
                classification="CONFIDENTIAL",
                allowed_roles=["ENGINEER", "MANAGER", "ADMIN", "OPERATOR", "AUDITOR"]
            ),
            DocumentChunk(
                chunk_id="pump_manual_01",
                filename="NOVA_Pump_CP9000_Maintenance_Manual.txt",
                file_type="txt",
                page_number=3,
                section="Technical Specifications",
                content="CENTRIFUGAL PUMP CP-9000 TECHNICAL & ENGINEERING MANUAL\n"
                        "Maximum rated operating speed: 3,600 RPM. Maximum continuous temperature limit: 85.0°C. Maximum vibration tolerance: 4.5 mm/s RMS. "
                        "Inspection procedures require checking outer casing housing for surface oxidation, pitting, and fatigue cracks.",
                department="ENGINEERING",
                classification="CONFIDENTIAL",
                allowed_roles=["ENGINEER", "MANAGER", "ADMIN", "OPERATOR", "AUDITOR"]
            ),
            DocumentChunk(
                chunk_id="mgr_strategy_01",
                filename="NOVA_Management_Q3_Budget_Strategy.txt",
                file_type="txt",
                page_number=1,
                section="Executive Compensation & Budget Allocation",
                content="CONFIDENTIAL MANAGER KNOWLEDGE: Executive budget allocation, plant manager compensation bonuses, and Q3 confidential operational strategy. "
                        "Access restricted to Management and Executive personnel.",
                department="MANAGEMENT",
                classification="CONFIDENTIAL",
                allowed_roles=["MANAGER", "ADMIN"]
            ),
            DocumentChunk(
                chunk_id="adm_keys_01",
                filename="NOVA_Admin_Security_Master_Keys.txt",
                file_type="txt",
                page_number=1,
                section="Root Infrastructure Credentials",
                content="CONFIDENTIAL ADMIN KNOWLEDGE: System root credentials, database encryption master keys, and datacenter air-gap security override codes. "
                        "Strictly restricted to System Administrators.",
                department="SECURITY",
                classification="RESTRICTED",
                allowed_roles=["ADMIN"]
            )
        ]
        if self.client and rest_models:
            try:
                info = self.client.get_collection(self.collection_name)
                if info.points_count == 0:
                    self.insert_chunks(default_docs)
            except Exception:
                self.insert_chunks(default_docs)


    def _ensure_collection(self):
        if self.client and rest_models:
            try:
                collections = [c.name for c in self.client.get_collections().collections]
                if self.collection_name not in collections:
                    self.client.create_collection(
                        collection_name=self.collection_name,
                        vectors_config=rest_models.VectorParams(
                            size=self.embedding_service.vector_dim,
                            distance=rest_models.Distance.COSINE
                        )
                    )
            except Exception as e:
                print(f"Warning: Qdrant collection init: {e}")

    def insert_chunks(self, chunks: List[DocumentChunk]):
        if not chunks:
            return

        texts = [chunk.content for chunk in chunks]
        embeddings = self.embedding_service.embed_documents(texts)

        if self.client and rest_models:
            points = []
            for idx, (chunk, vector) in enumerate(zip(chunks, embeddings)):
                payload = chunk.model_dump()
                points.append(
                    rest_models.PointStruct(
                        id=str(uuid.uuid5(uuid.NAMESPACE_DNS, chunk.chunk_id)),
                        vector=vector,
                        payload=payload
                    )
                )
            try:
                self.client.upsert(collection_name=self.collection_name, points=points)
            except Exception:
                pass

        for chunk in chunks:
            self.memory_store.append(chunk.model_dump())

    def search(
        self,
        query: str,
        user_role: str = "ENGINEER",
        top_k: int = 5,
        department: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        if not self.client or not rest_models:
            raise RuntimeError("QDRANT_UNAVAILABLE: Local Qdrant vector database client is not initialized or qdrant-client package is missing.")
        
        try:
            query_vector = self.embedding_service.embed_query(query)
            must_filters = [
                rest_models.FieldCondition(
                    key="allowed_roles",
                    match=rest_models.MatchValue(value=user_role)
                )
            ]
            if department:
                must_filters.append(
                    rest_models.FieldCondition(
                        key="department",
                        match=rest_models.MatchValue(value=department)
                    )
                )
            query_filter = rest_models.Filter(must=must_filters)
            if hasattr(self.client, "query_points"):
                response = self.client.query_points(
                    collection_name=self.collection_name,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=top_k
                )
                search_results = response.points
            elif hasattr(self.client, "search"):
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=top_k
                )
            else:
                raise RuntimeError("QdrantClient does not support search or query_points methods.")
            results = []
            for res in search_results:
                results.append({
                    "score": round(res.score, 4),
                    "chunk_id": res.payload.get("chunk_id"),
                    "filename": res.payload.get("filename"),
                    "page_number": res.payload.get("page_number"),
                    "section": res.payload.get("section"),
                    "content": res.payload.get("content"),
                    "department": res.payload.get("department"),
                    "classification": res.payload.get("classification")
                })
            return results
        except RuntimeError as re:
            raise re
        except Exception as e:
            raise RuntimeError(f"QDRANT_UNAVAILABLE: Qdrant vector database search failed: {str(e)}")
