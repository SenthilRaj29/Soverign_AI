# Sovereign AI Workbench — Frontend Walkthrough & User Guide

This document describes the design, architecture, workflows, and role-based views of the **Sovereign AI Workbench** React (Vite + TypeScript) frontend application, connected to the Phase 3 FastAPI + PostgreSQL backend.

---

## 1. Application Overview & Architecture

The frontend is a single-page application (SPA) built using **React 18**, **TypeScript**, **TailwindCSS**, and **Lucide React** icons. It communicates with the FastAPI backend running on `http://localhost:8000`.

### Key Security & Session Principles:
- **Authentication**: JWT Bearer tokens returned by `POST /api/auth/login`.
- **Session Storage**: JWT token and user profile objects are persisted in `sessionStorage` (`sovereign_jwt_token` and `sovereign_user`).
- **Server-Derived RBAC**: Every API request sends the `Authorization: Bearer <token>` header. The backend resolves identity, active status, and role directly from PostgreSQL.
- **Role Hierarchy**:
  1. `ENGINEER`: Query RAG knowledge base, view telemetry, view knowledge base files. Document upload is restricted.
  2. `MANAGER`: Query RAG, view telemetry, upload new confidential documents (`PENDING` -> `INDEXED` lifecycle tracking in PostgreSQL).
  3. `ADMIN`: All MANAGER capabilities, plus access to Sovereignty Telemetry metrics, administrative audit logs, and user management.

---

## 2. Screen-by-Screen Walkthrough

### Screen 1: Unauthenticated Login Page (`frontend_login.png`)
- **Purpose**: Authenticates industrial operators and administrators before granting access to confidential workspace tools.
- **Visible Elements**:
  - Header: **SOVEREIGN AI WORKBENCH** — *Offline Authentication & RBAC System*.
  - Username input field (`engineer`, `manager`, `admin`).
  - Password input field.
  - Action button: **"Sign In to Sovereign Workbench"**.
  - **Development Test Logins**: Quick shortcut buttons (`ENGINEER`, `MANAGER`, `ADMIN`) for fast role testing.
- **API Endpoint**: `POST /api/auth/login`.
- **Accessible By**: Public / Unauthenticated users.

---

### Screen 2: Authentication Error Alert (`frontend_login_error.png`)
- **Purpose**: Gracefully informs the user of authentication failures or backend database connectivity issues without exposing stack traces, credentials, or sensitive system details.
- **Visible Elements**:
  - Alert Banner: **"Authentication service temporarily unavailable."** or **"Invalid username or password."**
- **API Endpoint**: `POST /api/auth/login` (Returns HTTP 401 for bad credentials or HTTP 503 if PostgreSQL is offline).
- **Accessible By**: Public / Unauthenticated users.

---

### Screen 3: ENGINEER Dashboard (`frontend_engineer_dashboard.png`)
- **Purpose**: Primary workspace for industrial engineers to execute RAG queries and review safety procedures.
- **Visible Elements**:
  - Header showing authenticated user (`engineer`) and role badge (`ENGINEER`).
  - System Navigation (Agent Workspace, Sensor Telemetry Graph, Sovereignty Telemetry).
  - Industrial Task Input area ("Execute Industrial Task / Ask Knowledge Base").
  - Grounded Knowledge Base file list.
- **API Endpoint**: `GET /api/auth/me`, `POST /api/rag/ask`.
- **Accessible By**: `ENGINEER`, `MANAGER`, `ADMIN`.

---

### Screen 4: ENGINEER Document Upload Restriction (`frontend_documents_engineer.png`)
- **Purpose**: Enforces RBAC boundaries on document ingestion.
- **Visible Elements**:
  - Ingest Confidential Data section displaying a locked state:
    > **Upload Restricted** — *Your role (ENGINEER) cannot ingest new files. Log in as MANAGER or ADMIN to upload.*
- **API Endpoint**: `POST /api/documents/upload` (Enforces HTTP 403 Forbidden for `ENGINEER`).
- **Accessible By**: `ENGINEER` (View-only restriction notice).

---

### Screen 5: Sensor Telemetry Graph (`frontend_telemetry.png`)
- **Purpose**: Visualizes real-time operating metrics (temperature and vibration) for industrial machinery (e.g., Pump CP-9000).
- **Visible Elements**:
  - Real-time SVG temperature graph with threshold line (85.0°C).
  - Critical Anomaly Warning indicator (91.7°C).
  - Time-series data points with anomaly highlights.
- **API Endpoint**: `GET /api/telemetry/sensor-chart`.
- **Accessible By**: `ENGINEER`, `MANAGER`, `ADMIN`.

---

### Screen 6: RAG Query Execution & Verified Citations (`frontend_rag_working.png`)
- **Purpose**: Displays grounded LLM responses (Gemma 4) with 100% verified source citations from indexed vector storage.
- **Visible Elements**:
  - Grounded Answer Summary.
  - Grounded Source Citations (Filename, Section, Page number, Security Classification).
  - Execution Trace Timeline showing real-time latencies (Auth validation, Qdrant role filter, Gemma 4 completion).
- **API Endpoint**: `POST /api/rag/ask`.
- **Accessible By**: `ENGINEER`, `MANAGER`, `ADMIN`.

---

### Screen 7: Logout Action (`frontend_logout_login_screen.png`)
- **Purpose**: Clears active session state from `sessionStorage` and returns the user to the unauthenticated login screen.
- **Visible Elements**:
  - Header Logout button (`Sign Out`).
  - Redirection to initial Login screen with empty session.
- **API Endpoint**: Client-side session purge.
- **Accessible By**: All authenticated users.

---

### Screen 8: MANAGER Dashboard & File Ingestion (`frontend_manager_dashboard.png`, `frontend_manager_upload.png`)
- **Purpose**: Enables Managers to ingest new confidential documents into the RAG knowledge base.
- **Visible Elements**:
  - Header displaying `manager` user and `MANAGER` role badge (amber).
  - Active drag-and-drop document upload box ("Click or Drag File Here").
  - Accepted file formats (.pdf, .docx, .csv, .txt, .jpg, .png up to 50MB).
- **API Endpoint**: `POST /api/documents/upload`.
- **Accessible By**: `MANAGER`, `ADMIN`.

---

### Screen 9: ADMIN Sovereignty Telemetry Dashboard (`frontend_admin_dashboard.png`)
- **Purpose**: Administrative panel monitoring system sovereignty, zero cloud egress metrics, and PostgreSQL RBAC integrity.
- **Visible Elements**:
  - Header displaying `admin` user and `ADMIN` role badge (emerald).
  - Metric Cards:
    - **SERVER-ENFORCED RBAC**: `100% VERIFIED`
    - **EXTERNAL CLOUD EGRESS**: `0 BYTES`
- **API Endpoint**: `GET /api/system/sovereignty`, `GET /api/health/database`.
- **Accessible By**: `ADMIN`.
