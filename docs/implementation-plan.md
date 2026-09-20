# Implementation Plan & Execution Roadmap

## Sovereign On-Premise Agentic AI Workbench using Open-Weight Multimodal LLMs

### Phase Overview

This document outlines the detailed step-by-step implementation strategy for building the Sovereign On-Premise Agentic AI Workbench across 31 execution phases.

---

### Phase Breakdown & Execution Milestones

| Phase | Title | Key Deliverables | Primary Verification Method |
| :--- | :--- | :--- | :--- |
| **Phase 0** | Project & Repository Inspection | Architecture & Implementation Plan Docs | Manual Review & File Verification |
| **Phase 1** | Development Environment & Baseline | Monorepo layout, `.env.example`, Docker setup, startup scripts | `docker compose config`, service status check |
| **Phase 2** | Local Gemma & Ollama Integration | `LLMProvider`, `OllamaProvider`, `/api/llm/chat`, health endpoint | Pytest for Ollama mock & local connection check |
| **Phase 3** | Document Ingestion Pipeline | Parsers for PDF, DOCX, TXT, CSV, XLSX with metadata tagging | File parser unit tests & chunk inspection |
| **Phase 4** | Local OCR Service | PaddleOCR local integration, image text extractor, confidence scoring | OCR output verification on sample scanned image |
| **Phase 5** | Local Embedding Service | SentenceTransformers `EmbeddingService` with BGE/E5 local model | Vector dimension & embedding speed test |
| **Phase 6** | Local Qdrant Vector Store | Qdrant client, collection creation, RBAC document-level payload filter | Search test enforcing role permission filters |
| **Phase 7** | Offline RAG Pipeline | Query normalizer, RAG retrieval engine, context builder, non-hallucination prompt guard | RAG citation accuracy & grounding tests |
| **Phase 8** | Private Industrial Knowledge Base | Synthetic "NOVA INDUSTRIAL SYSTEMS" documents (Safety, Manuals, SOPs) | Ingest synthetic docs and verify RAG search |
| **Phase 9** | Industrial Data Analysis Engine | Python Pandas sensor data analyzer (outlier, rolling avg, thresholds) | Structured JSON output verification on CSV data |
| **Phase 10**| Industrial Dataset Integration | NASA C-MAPSS predictive maintenance dataset integration | Predictive maintenance analysis test |
| **Phase 11**| Multimodal Analysis Engine | Local vision analysis pipeline (Gemma Vision) for inspection photos | Multi-modal reasoning output test on sample image |
| **Phase 12**| Model Router & Modality Router | `ModelRouter` capability matrix, routing decision logger | Routing accuracy test for text vs vision vs code |
| **Phase 13**| Agent Orchestration | OpenWorker agent state machine, dynamic task planner, tool dispatch loop | End-to-end task breakdown test |
| **Phase 14**| Agent State Persistence | Task State Manager with DB/JSON schema, status tracking (PENDING, RUNNING, etc.) | Task state transition & pause/resume tests |
| **Phase 15**| Tool System Architecture | Tool interface definition, metadata self-discovery, registration harness | Tool discovery & parameter validation tests |
| **Phase 16**| Tool Permissions & Approval Gates | Risk levels (LOW, MEDIUM, HIGH, FORBIDDEN), human approval gate mechanism | Permission enforcement & approval gate tests |
| **Phase 17**| Sandboxed Python Execution | Ephemeral Docker sandbox container with `--net=none` and resource limits | Sandbox isolation & execution security tests |
| **Phase 18**| Automated Report Generation | Professional DOCX & PDF industrial report builders | Report rendering & layout validation |
| **Phase 19**| Audit Trail Engine | Immutable audit logging service, task event recorder, hash verification | `/api/audit/tasks/{task_id}` verification |
| **Phase 20**| Core Security & Auth | JWT auth, RBAC middleware, path traversal guard, input sanitizer | Security vulnerability & unauthorized access tests |
| **Phase 21**| Prompt Injection Defense | System policy demarcation, prompt sanitizer, untrusted content wrapper | Injection attempt & jailbreak resilience tests |
| **Phase 22**| Network Sovereignty Monitor | Outbound socket monitor, `/api/system/sovereignty` status endpoint | Egress verification test (zero cloud traffic) |
| **Phase 23**| Sovereignty & System Dashboard | Real-time backend status aggregator for local LLM, DB, vector store, network | Health telemetry API tests |
| **Phase 24**| Enterprise React Workbench UI | Vite + React + TS + Tailwind frontend, responsive layout, Chat, File drawer | Component rendering & user interaction flow |
| **Phase 25**| Execution Trace Visualization UI | Real-time step-by-step agent trace timeline component | Websocket trace streaming test |
| **Phase 26**| Async Task Processing & SSE | Background job queue, Server-Sent Events / WebSockets for long tasks | Non-blocking UI & task cancellation tests |
| **Phase 27**| LoRA Baseline & PEFT Evaluation | Evaluation dataset harness, optional HuggingFace PEFT adapter launcher | LoRA evaluation runner test |
| **Phase 28**| Comprehensive Evaluation Suite | Automated RAG relevance, hallucination rate, sandbox escape, sovereignty tests | Full evaluation runner execution |
| **Phase 29**| Automated Testing Pipeline | Pytest unit, integration, security, and edge-case test suite | `pytest` runner execution |
| **Phase 30**| Observability & Prometheus Metrics| Prometheus exporter, Grafana dashboard configuration | `/metrics` endpoint verification |
| **Phase 31**| SIH Master Demonstration Workflow| End-to-end industrial inspection, sensor analysis, RAG, report, audit & sovereignty proof | Full offline SIH demo execution |

---

### Verification Strategy
- **Automated Tests**: Unit and integration tests written in `pytest` for backend, `vitest` for frontend.
- **Security Tests**: Sandbox isolation tests verifying `--net=none` and path traversal defenses.
- **Sovereignty Tests**: Telemetry verification ensuring zero socket connections to external domains.
- **Manual Demonstration**: Verification of the master industrial inspection flow completely offline.
