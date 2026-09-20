# 🏆 Sovereign AI Workbench — Complete Project Explanation & Presentation Guide

---

## 🧠 1. The Core Problem & Our Sovereign Solution

### ❌ The Problem:
Enterprises (manufacturing plants, industrial facilities, defense organizations, healthcare centers) handle **confidential documents, inspection photos, sensor data, and proprietary manuals**.

Uploading this data to cloud AI services (like ChatGPT, Gemini, or external OCR/embedding APIs) introduces:
- **Data Leakage Risks**: Proprietary engineering knowledge leaving company servers.
- **Compliance Violations**: Defense, healthcare, and corporate privacy mandates (GDPR, HIPAA, ISO 27001).
- **External Provider Lock-in**: Loss of control over enterprise data and AI execution.

---

### 🔒 Our Solution:
A **Sovereign On-Premise Agentic AI Workbench** that operates **100% locally** inside the organization's internal server infrastructure.

- **Zero Cloud APIs**: Uses open-weight **Gemma 3** via Ollama.
- **Offline-First**: Operates completely disconnected from the internet once installed.
- **Local RAG**: Searches private company manuals using local vector database (Qdrant) and local embeddings (SentenceTransformers BGE/E5).
- **Local OCR**: Extracts text from scanned PDFs and inspection sheets locally (PaddleOCR).
- **Safe Data Analysis**: Executes Python code on sensor CSVs inside isolated Docker containers (`--net=none`).
- **Complete Auditability**: Cryptographic SHA-256 audit logging for every single action.

---

## 🏗️ 2. Step-by-Step Breakdown: What We Built & Why

```
                  USER (LEAD ENGINEER)
                           │
                           ▼
              ┌──────────────────────────┐
              │  REACT WORKBENCH FRONTEND │
              └────────────┬─────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │ FASTAPI BACKEND GATEWAY  │
              └────────────┬─────────────┘
                           │
                           ▼
              ┌──────────────────────────┐
              │ OPENWORKER AGENT BRAIN   │
              └────────────┬─────────────┘
                           │
             ┌─────────────┼──────────────┐
             ▼             ▼              ▼
       ┌──────────┐  ┌───────────┐  ┌────────────┐
       │   RAG    │  │  PANDAS   │  │   VISION   │
       │ (QDRANT) │  │  PYTHON   │  │  GEMMA 3   │
       └────┬─────┘  └─────┬─────┘  └─────┬──────┘
            │              │              │
            └──────────────┼──────────────┘
                           │
                           ▼
             ┌───────────────────────────┐
             │ AUTOMATED DOCX/PDF REPORT │
             │     + AUDIT TRAIL LOG     │
             └───────────────────────────┘
```

---

### **Step 1: Monorepo Architecture**
- **What We Built**: Clean separation between `frontend/`, `backend/`, `knowledge_base/`, `docker/`, and `reports/`.
- **Why We Chose It**: Modular, reproducible, easy to test, and easy to deploy across Linux/Ubuntu or Windows (WSL2).

---

### **Step 2: Local AI Model Engine (Gemma 3 via Ollama)**
- **What We Built**: `LLMProvider` abstract class and `OllamaProvider` implementation in `backend/app/llm/provider.py`.
- **Why We Chose Gemma 3**: It is Google DeepMind's state-of-the-art open-weight model with strong reasoning capabilities.
- **Why We Chose Ollama**: Serves Gemma 3 locally over HTTP (`http://localhost:11434`), guaranteeing 0 cloud requests.

---

### **Step 3: Document Ingestion Pipeline**
- **What We Built**: Parser in `backend/app/services/ingestion.py` for `.pdf`, `.docx`, `.csv`, `.xlsx`, and `.txt`.
- **Why We Chose PyMuPDF & python-docx**: Parses text in memory in milliseconds without calling external conversion services.
- **Metadata Tagging**: Every chunk retains `filename`, `page_number`, `section`, `department`, and `allowed_roles`.

---

### **Step 4: Local OCR Engine (PaddleOCR)**
- **What We Built**: `LocalOCRService` in `backend/app/ocr/ocr_service.py`.
- **Why We Chose PaddleOCR**: Processes scanned paper documents and inspection sheets on CPU/GPU locally without needing cloud computer vision APIs.

---

### **Step 5: Local Embedding Service (SentenceTransformers)**
- **What We Built**: `EmbeddingService` in `backend/app/rag/embedding_service.py`.
- **Why We Chose BGE / E5**: Top-performing open-weight embedding model (`BAAI/bge-small-en-v1.5`) running locally via HuggingFace `sentence-transformers`.

---

### **Step 6: Local Vector Database (Qdrant) + RBAC Filter**
- **What We Built**: `LocalVectorStore` in `backend/app/rag/vector_store.py`.
- **Why We Chose Qdrant**: Fast, open-source vector store running in a local Docker container (`localhost:6333`).
- **Role-Based Access Control (RBAC)**: Enforces payload filtering. An **Engineer** can search technical manuals, but if a chunk is marked `MANAGER_ONLY`, Qdrant automatically filters it out during the vector search!

---

### **Step 7: Offline RAG Engine**
- **What We Built**: `RAGPipeline` in `backend/app/rag/rag_pipeline.py`.
- **Why We Built It**: Forces Gemma 3 to answer using ONLY retrieved local manuals and explicitly cite sources (e.g., `[NOVA_Safety_SOP.txt, Page 2]`). If no relevant text is found, it explicitly states: *"Sufficient evidence was not found."* (Zero Hallucinations!).

---

### **Step 8: Synthetic Industrial Knowledge Base**
- **What We Built**: Synthetic company **NOVA INDUSTRIAL SYSTEMS** manuals (`NOVA_Safety_SOP_LOTO.txt`, `NOVA_Pump_CP9000_Maintenance_Manual.txt`) and sensor CSV dataset (`pump_sensor_data.csv`).
- **Why We Built It**: Demonstrates realistic industrial equipment troubleshooting safely without using real confidential enterprise data.

---

### **Step 9: Python Industrial Data Analyzer (Pandas)**
- **What We Built**: `PythonDataAnalyzer` in `backend/app/services/data_analyzer.py`.
- **Why We Chose Pandas**: LLMs are terrible at accurate numerical calculations! Our Python script calculates exact rolling statistics, max temperatures, and threshold violations (e.g., Temperature > 85°C critical limit). Gemma 3 then explains the Python calculations in plain English.

---

### **Step 10: Multimodal Vision Inspection Service**
- **What We Built**: `MultimodalVisionService` in `backend/app/services/vision_service.py`.
- **Why We Built It**: Uses Gemma Vision to inspect equipment damage photographs (surface pitting, rust, hairline fatigue fractures) while separating **Observed Visual Facts** from **Model Interpretation**.

---

### **Step 11: Model & Modality Router**
- **What We Built**: `ModelRouter` in `backend/app/router/model_router.py`.
- **Why We Built It**: Automatically routes text queries to Text Gemma, photo inspection tasks to Vision Gemma, and sensor processing to Python Pandas.

---

### **Step 12: OpenWorker Agent Orchestrator (The Master Brain)**
- **What We Built**: `OpenWorkerAgentOrchestrator` in `backend/app/agents/orchestrator.py` inspired by Andrew Ng's OpenWorker coworker pattern.
- **How It Works**:
  1. Parses task objective.
  2. Generates an 11-step execution plan.
  3. Executes tools dynamically (Python, Vision, RAG).
  4. Synthesizes findings and recommendations.
  5. Triggers automated report creation.
  6. Logs complete execution trace and audit trails.

---

### **Step 13: Automated Report Generator (DOCX & PDF)**
- **What We Built**: `ReportGenerator` in `backend/app/reports/report_generator.py`.
- **Why We Chose ReportLab & python-docx**: Automatically creates official, professional industrial maintenance approval notes in `.docx` and `.pdf` formats on the local filesystem.

---

### **Step 14: Cryptographic Audit Trail Engine**
- **What We Built**: `AuditService` in `backend/app/audit/audit_service.py`.
- **Why We Built It**: Computes a SHA-256 hash checksum for every tool execution, user action, model call, and generated file, storing them in local `.jsonl` audit records for compliance.

---

### **Step 15: Network Sovereignty Telemetry Monitor**
- **What We Built**: Telemetry API at `/api/system/sovereignty`.
- **Why It Matters for Judges**: Verifies live in real-time that **0 external cloud API calls** were made.

---

### **Step 16: Enterprise React Workbench UI**
- **What We Built**: Modern dark-mode workspace in `frontend/src/App.tsx`.
- **Key Features**:
  - **Left Panel**: Confidential file explorer & knowledge base.
  - **Center Panel**: Task objective input & AI synthesis output.
  - **Right Panel**: Real-time **Execution Trace Timeline** (shows duration in milliseconds for every step).
  - **Top Navigation Bar**: Live **Network Isolation Status** badge.

---

## 🔄 3. Complete End-to-End Demonstration Workflow

Here is what happens when you run a demo for SIH evaluation:

```
[1. UPLOAD CONFIDENTIAL FILES]
 ├── pump_inspection_scan.pdf
 ├── pump_sensor_data.csv
 └── pump_damage.jpg

[2. ENTER INDUSTRIAL OBJECTIVE]
 "Analyze this equipment, check safety procedures from private knowledge base,
  analyze sensor data, inspect image, and prepare a maintenance approval note."

[3. OFFLINE AGENT EXECUTION LOOP]
 ├── STEP 1: Reads PDF using PyMuPDF locally.
 ├── STEP 2: Runs Python Pandas on CSV ➔ Detects critical violation (Temp 91.7°C > 85°C limit).
 ├── STEP 3: Runs Multimodal Vision on damage photo ➔ Detects surface pitting & stress fracture.
 ├── STEP 4: Runs RAG on local Qdrant ➔ Retrieves LOTO Procedure NOVA-SOP-2024-08 Section 2.
 ├── STEP 5: Gemma 3 combines evidence & formulates emergency recommendations.
 ├── STEP 6: Report Generator creates DOCX and PDF maintenance approval notes.
 └── STEP 7: Audit Service logs cryptographic SHA-256 trail.

[4. FINAL OUTPUT]
 - Real-time execution trace displayed in UI.
 - Downloadable DOCX and PDF reports stored locally.
 - Live Sovereignty Panel proves 0 external network bytes transferred!
```

---

## 🚀 4. How to Run the Project (3 Simple Commands)

1. **Start Infrastructure (Postgres & Qdrant)**
   ```bash
   docker compose up -d
   ```

2. **Start Backend API**
   ```bash
   cd backend
   uvicorn main:app --reload --port 8000
   ```

3. **Start React Frontend UI**
   ```bash
   cd frontend
   npm run dev
   ```

Open `http://localhost:5173` in your browser!
