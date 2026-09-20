import time
from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.auth.models import LoginRequest, ChangePasswordRequest, Token, User, UserRole
from app.auth.security import create_access_token, verify_password, hash_password
from app.auth.dependencies import get_current_user
from app.db.session import get_db
from app.db.repositories import UserRepository
from app.audit.audit_service import AuditService

router = APIRouter(prefix="/api/auth", tags=["Authentication"])
audit_service = AuditService()

@router.post("/login", response_model=Token)
async def login_endpoint(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user_db = await UserRepository.get_by_username(db, request.username)
    except Exception as e:
        audit_service.record_event(
            task_id="auth_event",
            user_id=request.username if request.username else "anonymous",
            action="LOGIN_FAILURE",
            component="LOGIN_ENDPOINT",
            details={"reason": "Database connection failure", "error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable."
        )

    if not user_db or not user_db.is_active or not verify_password(request.password, user_db.password_hash):
        audit_service.record_event(
            task_id="auth_event",
            user_id=request.username if request.username else "anonymous",
            action="LOGIN_FAILURE",
            component="LOGIN_ENDPOINT",
            details={"reason": "Invalid credentials or inactive account"}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    role_val = user_db.role.value if hasattr(user_db.role, "value") else str(user_db.role)
    token = create_access_token(data={
        "sub": user_db.id,
        "username": user_db.username,
        "role": role_val
    })

    audit_service.record_event(
        task_id="auth_event",
        user_id=user_db.username,
        action="LOGIN_SUCCESS",
        component="LOGIN_ENDPOINT",
        details={"role": role_val}
    )

    created_ts = user_db.created_at if (hasattr(user_db, "created_at") and user_db.created_at is not None) else time.time()
    user_public = User(
        id=user_db.id,
        username=user_db.username,
        role=UserRole(role_val),
        is_active=user_db.is_active,
        created_at=created_ts
    )

    return Token(
        access_token=token,
        token_type="bearer",
        user=user_public
    )

@router.get("/me", response_model=User)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/change-password")
async def change_password_endpoint(
    request: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        user_db = await UserRepository.get_by_id(db, current_user.id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable."
        )

    if not user_db or not verify_password(request.current_password, user_db.password_hash):
        audit_service.record_event(
            task_id="auth_event",
            user_id=current_user.username,
            action="PASSWORD_CHANGE_FAILED",
            component="CHANGE_PASSWORD_ENDPOINT",
            details={"reason": "Invalid current password provided"}
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is invalid."
        )

    new_hash = hash_password(request.new_password)
    await UserRepository.change_password(db, current_user.id, new_hash)

    audit_service.record_event(
        task_id="auth_event",
        user_id=current_user.username,
        action="PASSWORD_CHANGED",
        component="CHANGE_PASSWORD_ENDPOINT",
        details={"status": "SUCCESS"}
    )

    return {"status": "SUCCESS", "message": "Password updated successfully."}
