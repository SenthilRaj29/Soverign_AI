import sys
import os
import time
import pytest
from fastapi.testclient import TestClient
from datetime import timedelta

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from main import app
from app.auth.security import create_access_token, hash_password, verify_password
from app.auth.models import UserRole
from app.db.models import UserModel, DocumentModel
from app.db.repositories import UserRepository, DocumentRepository
from app.audit.audit_service import AuditService

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_mock_db_users(monkeypatch):
    """Fixture ensuring PostgreSQL UserRepository returns test accounts for Phase 2 regression suite."""
    now = time.time()
    eng_pass = hash_password(os.getenv("DEV_ENGINEER_PASSWORD", "Engineer@123"))
    mgr_pass = hash_password(os.getenv("DEV_MANAGER_PASSWORD", "Manager@123"))
    adm_pass = hash_password(os.getenv("DEV_ADMIN_PASSWORD", "Admin@123"))

    eng_user = UserModel(id="usr_eng_01", username="engineer", password_hash=eng_pass, role=UserRole.ENGINEER, is_active=True, created_at=now, updated_at=now)
    mgr_user = UserModel(id="usr_mgr_01", username="manager", password_hash=mgr_pass, role=UserRole.MANAGER, is_active=True, created_at=now, updated_at=now)
    adm_user = UserModel(id="usr_adm_01", username="admin", password_hash=adm_pass, role=UserRole.ADMIN, is_active=True, created_at=now, updated_at=now)

    users_map = {
        "engineer": eng_user,
        "manager": mgr_user,
        "admin": adm_user
    }

    async def mock_get_by_username(db, username):
        return users_map.get(username.lower()) if username else None

    async def mock_get_by_id(db, user_id):
        for u in users_map.values():
            if u.id == user_id:
                return u
        return None

    async def mock_get_doc(db, filename):
        return None

    async def mock_create_doc(db, **kwargs):
        return DocumentModel(
            id="doc_test_01",
            filename=kwargs.get("filename", "test.txt"),
            file_type=kwargs.get("file_type", "txt"),
            uploaded_by=kwargs.get("uploaded_by", "usr_adm_01"),
            department=kwargs.get("department", "ENGINEERING"),
            classification=kwargs.get("classification", "CONFIDENTIAL"),
            status=kwargs.get("status", "PENDING"),
            created_at=now,
            updated_at=now
        )

    async def mock_update_doc_status(db, filename, status):
        return DocumentModel(
            id="doc_test_01",
            filename=filename,
            file_type="txt",
            uploaded_by="usr_adm_01",
            department="ENGINEERING",
            classification="CONFIDENTIAL",
            status=status,
            created_at=now,
            updated_at=now
        )

    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_by_username)
    monkeypatch.setattr(UserRepository, "get_by_id", mock_get_by_id)
    monkeypatch.setattr(DocumentRepository, "get_by_filename", mock_get_doc)
    monkeypatch.setattr(DocumentRepository, "create_document", mock_create_doc)
    monkeypatch.setattr(DocumentRepository, "update_status", mock_update_doc_status)

# --- AUTH-01: Valid Login ---
def test_auth_01_valid_login():
    response = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": os.getenv("DEV_ENGINEER_PASSWORD", "Engineer@123")
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "engineer"
    assert data["user"]["role"] == "ENGINEER"
    # Ensure password and hash are NOT returned
    assert "password" not in data["user"]
    assert "password_hash" not in data["user"]

# --- AUTH-02: Invalid Password ---
def test_auth_02_invalid_password():
    response = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": "WrongPassword123!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."

# --- AUTH-03: Unknown Username ---
def test_auth_03_unknown_username():
    response = client.post("/api/auth/login", json={
        "username": "nonexistent_user",
        "password": "Password123!"
    })
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password."

# --- AUTH-04: Missing Token ---
def test_auth_04_missing_token():
    response = client.post("/api/rag/ask", json={
        "question": "What is the LOTO procedure?"
    })
    assert response.status_code == 401

# --- AUTH-05: Invalid Token ---
def test_auth_05_invalid_token():
    headers = {"Authorization": "Bearer invalid_garbage_token_string"}
    response = client.post("/api/rag/ask", json={
        "question": "What is the LOTO procedure?"
    }, headers=headers)
    assert response.status_code == 401

# --- AUTH-06: Expired Token ---
def test_auth_06_expired_token():
    expired_token = create_access_token(
        data={"sub": "usr_eng_01", "username": "engineer", "role": "ENGINEER"},
        expires_delta=timedelta(minutes=-10)
    )
    headers = {"Authorization": f"Bearer {expired_token}"}
    response = client.post("/api/rag/ask", json={
        "question": "What is the LOTO procedure?"
    }, headers=headers)
    assert response.status_code == 401

# --- AUTH-07: Inactive User ---
def test_auth_07_inactive_user(monkeypatch):
    now = time.time()
    eng_pass = hash_password(os.getenv("DEV_ENGINEER_PASSWORD", "Engineer@123"))
    inact_user = UserModel(id="usr_eng_01", username="engineer", password_hash=eng_pass, role=UserRole.ENGINEER, is_active=False, created_at=now, updated_at=now)

    async def mock_inact(db, username):
        return inact_user

    monkeypatch.setattr(UserRepository, "get_by_username", mock_inact)

    login_res = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": os.getenv("DEV_ENGINEER_PASSWORD", "Engineer@123")
    })
    assert login_res.status_code == 401

# --- AUTH-08: ENGINEER Access ---
def test_auth_08_engineer_access():
    login_res = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": os.getenv("DEV_ENGINEER_PASSWORD", "Engineer@123")
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    res = client.get("/api/system/sovereignty", headers=headers)
    assert res.status_code == 200
    assert res.json()["authenticated_user"] == "engineer"
    assert res.json()["authenticated_role"] == "ENGINEER"

# --- AUTH-09 & AUTH-10: MANAGER and ADMIN RBAC Checks ---
def test_auth_09_manager_access():
    login_res = client.post("/api/auth/login", json={
        "username": "manager",
        "password": os.getenv("DEV_MANAGER_PASSWORD", "Manager@123")
    })
    mgr_token = login_res.json()["access_token"]
    mgr_headers = {"Authorization": f"Bearer {mgr_token}"}

    res = client.get("/api/audit/tasks/task_test_01", headers=mgr_headers)
    assert res.status_code == 200

def test_auth_10_admin_access():
    login_res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": os.getenv("DEV_ADMIN_PASSWORD", "Admin@123")
    })
    adm_token = login_res.json()["access_token"]
    adm_headers = {"Authorization": f"Bearer {adm_token}"}

    res = client.get("/api/audit/tasks/task_test_01", headers=adm_headers)
    assert res.status_code == 200

# --- AUTH-11 & AUTH-12: Role Escalation Prevention ---
def test_auth_11_role_escalation_attempt_rejected():
    login_res = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": os.getenv("DEV_ENGINEER_PASSWORD", "Engineer@123")
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "question": "What is the manager confidential strategy?",
        "user_role": "ADMIN"
    }
    response = client.post("/api/rag/ask", json=payload, headers=headers)
    assert response.status_code == 422

def test_auth_12_role_escalation_attempt_with_manager_role():
    login_res = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": os.getenv("DEV_ENGINEER_PASSWORD", "Engineer@123")
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "question": "What is the manager bonus strategy?",
        "user_role": "MANAGER"
    }
    response = client.post("/api/rag/ask", json=payload, headers=headers)
    assert response.status_code == 422

# --- AUTH-13: Unauthenticated RAG Request Rejected ---
def test_auth_13_unauthenticated_rag_rejected():
    response = client.post("/api/rag/ask", json={"question": "LOTO shutdown"})
    assert response.status_code == 401

# --- AUTH-14 & AUTH-15: Document Upload Protection ---
def test_auth_14_unauthorized_upload_rejected():
    login_res = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": os.getenv("DEV_ENGINEER_PASSWORD", "Engineer@123")
    })
    eng_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {eng_token}"}

    files = {"file": ("test_doc.txt", b"Test content", "text/plain")}
    res = client.post("/api/documents/upload", files=files, headers=headers)
    assert res.status_code == 403
    assert "Access denied" in res.json()["detail"]

def test_auth_15_authorized_upload_success():
    login_res = client.post("/api/auth/login", json={
        "username": "admin",
        "password": os.getenv("DEV_ADMIN_PASSWORD", "Admin@123")
    })
    adm_token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {adm_token}"}

    files = {"file": ("admin_test_sop.txt", b"Admin test document content", "text/plain")}
    res = client.post("/api/documents/upload", files=files, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"
    assert res.json()["uploaded_by"] == "admin"

# --- AUTH-16: Logout Concept ---
def test_auth_16_logout_concept():
    login_res = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": os.getenv("DEV_ENGINEER_PASSWORD", "Engineer@123")
    })
    token = login_res.json()["access_token"]
    assert token is not None

# --- AUTH-17: Password Hash Never Exposed ---
def test_auth_17_password_hash_never_exposed():
    login_res = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": os.getenv("DEV_ENGINEER_PASSWORD", "Engineer@123")
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me_res = client.get("/api/auth/me", headers=headers)
    assert me_res.status_code == 200
    user_data = me_res.json()
    assert "password" not in user_data
    assert "password_hash" not in user_data

# --- AUTH-18: Passwords and Hashes Never Written to Audit Logs ---
def test_auth_18_no_passwords_in_audit_logs():
    audit_srv = AuditService()
    event = audit_srv.record_event(
        task_id="test_log",
        user_id="engineer",
        action="TEST_ACTION",
        component="TEST_COMP",
        details={
            "username": "engineer",
            "password": "SecretPassword123!",
            "password_hash": "$2b$12$hash_string",
            "access_token": "bearer_token_xyz"
        }
    )
    assert event.details["password"] == "[REDACTED_SENSITIVE_DATA]"
    assert event.details["password_hash"] == "[REDACTED_SENSITIVE_DATA]"
    assert event.details["access_token"] == "[REDACTED_SENSITIVE_DATA]"

    filepath = os.path.join(audit_srv.log_dir, "audit_test_log.jsonl")
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            assert "SecretPassword123!" not in content
            assert "$2b$12$hash_string" not in content
            assert "bearer_token_xyz" not in content
