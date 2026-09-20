# Sovereign On-Premise Agentic AI Workbench

> **Confidential Industrial Work powered by Open-Weight Multimodal LLMs (Gemma 3)**

## Overview

The **Sovereign On-Premise Agentic AI Workbench** allows enterprise, industrial, healthcare, and defense organizations to run advanced agentic AI workflows completely on-premise with zero cloud data egress.

### Key Capabilities
- **100% Local Inference**: Runs Gemma 3 locally via Ollama.
- **Offline RAG Engine**: Search private organizational documents using local SentenceTransformers and local Qdrant Vector Store.
- **Local OCR Engine**: Process scanned PDFs and inspection documents locally with PaddleOCR.
- **Sandboxed Data Analysis**: Execute Python code safely in isolated Docker containers with network access blocked.
- **Multimodal Visual Inspection**: Analyze equipment photos and industrial scans with local Gemma vision.
- **OpenWorker Agent Core**: Multi-step reasoning, dynamic tool selection, and execution trace recording.
- **Full Security & Auditability**: RBAC permissions, document-level authorization, and immutable task audit logging.
- **Sovereignty Dashboard**: Real-time telemetry proving zero external cloud API calls.

---

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Ollama (`ollama serve`)

### Installation & Local Setup

1. **Clone & Environment Setup**
   ```bash
   cp .env.example .env
   ```

2. **Start Infrastructure Services (Postgres, Qdrant, Prometheus, Grafana)**
   ```bash
   docker compose up -d
   ```

3. **Pull Local Gemma Model**
   ```bash
   ollama pull gemma3:latest
   ```

4. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   uvicorn app.main:app --reload --port 8000
   ```

5. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

---

## Verification & Health Check

- **Backend Health**: `GET http://localhost:8000/health`
- **Sovereignty Status**: `GET http://localhost:8000/api/system/sovereignty`
- **Qdrant Vector DB**: `http://localhost:6333/dashboard`
- **Prometheus Metrics**: `http://localhost:9090`
