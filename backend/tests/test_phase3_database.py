import sys
import os
import time
import asyncio
import pytest

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from main import app
from app.db.database import check_database_connection
from app.db.models import UserModel, AuditEventModel, DocumentModel
from app.db.repositories import UserRepository, AuditRepository, DocumentRepository
from app.auth.models import UserRole
from app.auth.security import create_access_token, hash_password, verify_password
from app.audit.audit_service import AuditService

client = TestClient(app)

# --- DATABASE-01: Database Connection Health Check ---
def test_database_01_connection():
    res = client.get("/api/health/database")
    assert res.status_code in [200, 503]
    if res.status_code == 200:
        assert res.json()["status"] == "healthy"
        assert res.json()["database"] == "postgresql"
    else:
        assert res.json()["status"] == "unhealthy"
        assert "Database connection" in res.json()["detail"]

# --- DATABASE-02: Database Connection Failure Returns HTTP 503 ---
def test_database_02_unavailable_behavior(monkeypatch):
    """Verify HTTP 503 service unavailable response when DB connection fails."""
    async def mock_get_by_username(*args, **kwargs):
        raise ConnectionError("Database connection refused")

    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_by_username)
    response = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": "Engineer@123"
    })
    assert response.status_code == 503
    assert "Authentication service temporarily unavailable" in response.json()["detail"]

# --- DATABASE-03: User Persistence Model & Password Hash Security ---
def test_database_03_user_persistence_model():
    hashed = hash_password("Engineer@123")
    user = UserModel(
        id="usr_eng_01",
        username="engineer",
        password_hash=hashed,
        role=UserRole.ENGINEER,
        is_active=True,
        created_at=time.time(),
        updated_at=time.time()
    )
    assert user.id == "usr_eng_01"
    assert user.username == "engineer"
    assert user.role == UserRole.ENGINEER
    assert user.password_hash.startswith("$2b$") or len(user.password_hash) > 20
    assert "Engineer@123" not in user.password_hash

# --- DATABASE-04: Duplicate Username Rejection Logic ---
def test_database_04_duplicate_username_logic(monkeypatch):
    """Verify Admin POST /api/admin/users rejects duplicate username with HTTP 400."""
    now = time.time()
    async def mock_get_by_username(db, username):
        if username == "admin":
            return UserModel(id="usr_adm_01", username="admin", password_hash=hash_password("Admin@123"), role=UserRole.ADMIN, is_active=True, created_at=now, updated_at=now)
        if username == "duplicate_user":
            return UserModel(id="usr_existing_01", username="duplicate_user", password_hash=hash_password("Pass123!"), role=UserRole.ENGINEER, is_active=True, created_at=now, updated_at=now)
        return None

    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_by_username)
    adm_token = create_access_token({"sub": "usr_adm_01", "username": "admin", "role": "ADMIN"})
    headers = {"Authorization": f"Bearer {adm_token}"}

    res = client.post("/api/admin/users", json={
        "username": "duplicate_user",
        "password": "NewPassword123!",
        "role": "ENGINEER"
    }, headers=headers)
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]

# --- DATABASE-05: Password Hash Persisted, Plaintext Absent ---
def test_database_05_password_hash_never_exposed():
    hashed = hash_password("SuperSecretPass123!")
    assert verify_password("SuperSecretPass123!", hashed) is True
    assert verify_password("WrongPass", hashed) is False
    assert "SuperSecretPass123!" not in hashed

# --- DATABASE-06: Valid Login Returns Token & Public User ---
def test_database_06_valid_login_endpoint(monkeypatch):
    hashed = hash_password("Engineer@123")
    now = time.time()
    mock_eng = UserModel(id="usr_eng_01", username="engineer", password_hash=hashed, role=UserRole.ENGINEER, is_active=True, created_at=now, updated_at=now)

    async def mock_get_eng(*args, **kwargs):
        return mock_eng

    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_eng)

    res = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": "Engineer@123"
    })
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["user"]["username"] == "engineer"
    assert data["user"]["role"] == "ENGINEER"
    assert "password_hash" not in data["user"]

# --- DATABASE-07: Invalid Password Rejected ---
def test_database_07_invalid_password_endpoint(monkeypatch):
    hashed = hash_password("Engineer@123")
    now = time.time()
    mock_eng = UserModel(id="usr_eng_01", username="engineer", password_hash=hashed, role=UserRole.ENGINEER, is_active=True, created_at=now, updated_at=now)

    async def mock_get_eng(*args, **kwargs):
        return mock_eng

    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_eng)

    res = client.post("/api/auth/login", json={
        "username": "engineer",
        "password": "WrongPassword123!"
    })
    assert res.status_code == 401
    assert res.json()["detail"] == "Invalid username or password."

# --- DATABASE-08: Inactive User Rejected ---
def test_database_08_inactive_user_rejected(monkeypatch):
    hashed = hash_password("Pass123!")
    now = time.time()
    inactive_usr = UserModel(id="usr_inact_01", username="inactive_user", password_hash=hashed, role=UserRole.ENGINEER, is_active=False, created_at=now, updated_at=now)

    async def mock_get_inact(*args, **kwargs):
        return inactive_usr

    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_inact)

    res = client.post("/api/auth/login", json={"username": "inactive_user", "password": "Pass123!"})
    assert res.status_code == 401

# --- DATABASE-09 & DATABASE-10: Dynamic Current Role Resolution ---
def test_database_09_and_10_dynamic_role_resolution(monkeypatch):
    now = time.time()
    user_state = UserModel(id="usr_dynamic_01", username="dynamic_user", password_hash=hash_password("Pass123!"), role=UserRole.ENGINEER, is_active=True, created_at=now, updated_at=now)

    async def mock_get_user(*args, **kwargs):
        return user_state

    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_user)

    token = create_access_token({"sub": "usr_dynamic_01", "username": "dynamic_user", "role": "ENGINEER"})
    headers = {"Authorization": f"Bearer {token}"}

    # Initial check -> ENGINEER
    res1 = client.get("/api/auth/me", headers=headers)
    assert res1.status_code == 200
    assert res1.json()["role"] == "ENGINEER"

    # Update database state to MANAGER
    user_state.role = UserRole.MANAGER

    # Re-query using the same JWT -> dynamically resolves to MANAGER
    res2 = client.get("/api/auth/me", headers=headers)
    assert res2.status_code == 200
    assert res2.json()["role"] == "MANAGER"

# --- DATABASE-11 & DATABASE-12: Admin User Creation & Non-Admin Rejection ---
def test_database_11_and_12_admin_user_creation(monkeypatch):
    now = time.time()
    async def mock_get_user(db, username):
        if username == "engineer":
            return UserModel(id="usr_eng_01", username="engineer", password_hash=hash_password("Pass"), role=UserRole.ENGINEER, is_active=True, created_at=now, updated_at=now)
        if username == "admin":
            return UserModel(id="usr_adm_01", username="admin", password_hash=hash_password("Pass"), role=UserRole.ADMIN, is_active=True, created_at=now, updated_at=now)
        return None

    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_user)

    # Engineer token -> 403
    eng_token = create_access_token({"sub": "usr_eng_01", "username": "engineer", "role": "ENGINEER"})
    res_eng = client.post("/api/admin/users", json={"username": "new_usr", "password": "Password123!", "role": "ENGINEER"}, headers={"Authorization": f"Bearer {eng_token}"})
    assert res_eng.status_code == 403

    # Admin token -> 201
    async def mock_create_user(*args, **kwargs):
        return UserModel(id="usr_new_01", username="new_usr", password_hash=hash_password("Password123!"), role=UserRole.ENGINEER, is_active=True, created_at=now, updated_at=now)

    monkeypatch.setattr(UserRepository, "create_user", mock_create_user)
    adm_token = create_access_token({"sub": "usr_adm_01", "username": "admin", "role": "ADMIN"})
    res_adm = client.post("/api/admin/users", json={"username": "new_usr", "password": "Password123!", "role": "ENGINEER"}, headers={"Authorization": f"Bearer {adm_token}"})
    assert res_adm.status_code == 201
    assert res_adm.json()["username"] == "new_usr"

# --- DATABASE-13 & DATABASE-14: Admin Deactivation ---
def test_database_13_and_14_admin_deactivation(monkeypatch):
    now = time.time()
    target_user = UserModel(id="usr_target_01", username="target_user", password_hash=hash_password("Pass123!"), role=UserRole.ENGINEER, is_active=True, created_at=now, updated_at=now)
    adm_user = UserModel(id="usr_adm_01", username="admin", password_hash=hash_password("Pass123!"), role=UserRole.ADMIN, is_active=True, created_at=now, updated_at=now)

    async def mock_get_id(db, user_id):
        if user_id == "usr_adm_01": return adm_user
        if user_id == "usr_target_01": return target_user
        return None

    async def mock_get_uname(db, username):
        if username == "admin": return adm_user
        if username == "target_user": return target_user
        return None

    async def mock_update_user(db, user_id, role=None, is_active=None):
        if is_active is not None: target_user.is_active = is_active
        return target_user

    monkeypatch.setattr(UserRepository, "get_by_id", mock_get_id)
    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_uname)
    monkeypatch.setattr(UserRepository, "update_user", mock_update_user)

    adm_token = create_access_token({"sub": "usr_adm_01", "username": "admin", "role": "ADMIN"})
    headers = {"Authorization": f"Bearer {adm_token}"}

    # Deactivate user
    res = client.patch("/api/admin/users/usr_target_01", json={"is_active": False}, headers=headers)
    assert res.status_code == 200
    assert res.json()["is_active"] is False

    # Login attempt of deactivated user fails
    async def mock_get_deact(db, username):
        return target_user

    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_deact)
    login_res = client.post("/api/auth/login", json={"username": "target_user", "password": "Pass123!"})
    assert login_res.status_code == 401

# --- DATABASE-15 & DATABASE-16: Password Change Endpoint ---
def test_database_15_and_16_password_change(monkeypatch):
    now = time.time()
    hashed_old = hash_password("OldPass123!")
    user_record = UserModel(id="usr_change_01", username="change_user", password_hash=hashed_old, role=UserRole.ENGINEER, is_active=True, created_at=now, updated_at=now)

    async def mock_get_id(db, user_id):
        return user_record

    async def mock_get_uname(db, username):
        return user_record

    async def mock_change_pass(db, user_id, new_hash):
        user_record.password_hash = new_hash
        return True

    monkeypatch.setattr(UserRepository, "get_by_id", mock_get_id)
    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_uname)
    monkeypatch.setattr(UserRepository, "change_password", mock_change_pass)

    user_token = create_access_token({"sub": "usr_change_01", "username": "change_user", "role": "ENGINEER"})
    headers = {"Authorization": f"Bearer {user_token}"}

    # Execute password change
    res = client.post("/api/auth/change-password", json={
        "current_password": "OldPass123!",
        "new_password": "NewBrandPass123!"
    }, headers=headers)
    assert res.status_code == 200
    assert res.json()["status"] == "SUCCESS"

    # Verify old password is now rejected
    login_old = client.post("/api/auth/login", json={"username": "change_user", "password": "OldPass123!"})
    assert login_old.status_code == 401

    # Verify new password is accepted
    login_new = client.post("/api/auth/login", json={"username": "change_user", "password": "NewBrandPass123!"})
    assert login_new.status_code == 200

# --- DATABASE-17: Audit Sanitization ---
def test_database_17_audit_sanitization():
    srv = AuditService()
    event = srv.record_event(
        task_id="sec_test",
        user_id="admin",
        action="TEST_ACTION",
        component="TEST_COMP",
        details={
            "username": "admin",
            "password": "SuperSecretPassword123!",
            "password_hash": "$2b$12$fakehash",
            "access_token": "secret_jwt_token"
        }
    )
    assert event.details["password"] == "[REDACTED_SENSITIVE_DATA]"
    assert event.details["password_hash"] == "[REDACTED_SENSITIVE_DATA]"
    assert event.details["access_token"] == "[REDACTED_SENSITIVE_DATA]"

# --- DATABASE-18 & DATABASE-19: Document Metadata Model & Lifecycle ---
def test_database_18_and_19_document_metadata_model():
    doc = DocumentModel(
        id="doc_01",
        filename="pump_maintenance.pdf",
        file_type="pdf",
        uploaded_by="usr_adm_01",
        department="ENGINEERING",
        classification="CONFIDENTIAL",
        status="PENDING",
        created_at=time.time(),
        updated_at=time.time()
    )
    assert doc.status == "PENDING"
    doc.status = "INDEXED"
    assert doc.status == "INDEXED"

# --- DATABASE-20: Admin Self-Protection Constraints ---
def test_database_20_admin_self_protection(monkeypatch):
    now = time.time()
    adm_user = UserModel(id="usr_adm_01", username="admin", password_hash=hash_password("Pass123!"), role=UserRole.ADMIN, is_active=True, created_at=now, updated_at=now)

    async def mock_get_id(db, user_id):
        return adm_user

    async def mock_get_uname(db, username):
        return adm_user

    async def mock_count_admins(db):
        return 1

    monkeypatch.setattr(UserRepository, "get_by_id", mock_get_id)
    monkeypatch.setattr(UserRepository, "get_by_username", mock_get_uname)
    monkeypatch.setattr(UserRepository, "count_active_admins", mock_count_admins)

    adm_token = create_access_token({"sub": "usr_adm_01", "username": "admin", "role": "ADMIN"})
    headers = {"Authorization": f"Bearer {adm_token}"}

    # Attempt self-deactivation -> 400
    res_deact = client.patch("/api/admin/users/usr_adm_01", json={"is_active": False}, headers=headers)
    assert res_deact.status_code == 400
    assert "cannot deactivate their own" in res_deact.json()["detail"]

    # Attempt self-demotion -> 400
    res_demote = client.patch("/api/admin/users/usr_adm_01", json={"role": "ENGINEER"}, headers=headers)
    assert res_demote.status_code == 400
    assert "cannot revoke their own ADMIN role" in res_demote.json()["detail"]
