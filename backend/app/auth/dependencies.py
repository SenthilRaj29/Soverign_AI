import time
from typing import List, Union
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserRole
from app.auth.security import decode_access_token
from app.db.session import get_db
from app.db.repositories import UserRepository
from app.audit.audit_service import AuditService

security_bearer = HTTPBearer(auto_error=True)
audit_service = AuditService()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security_bearer),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    FastAPI dependency to authenticate requests using JWT Bearer token and resolve identity from PostgreSQL.
    """
    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token or expired session.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_access_token(token)
        username: str = payload.get("username")
        user_id: str = payload.get("sub")
        if username is None or user_id is None:
            audit_service.record_event(
                task_id="auth_event",
                user_id="anonymous",
                action="TOKEN_INVALID",
                component="AUTH_DEPENDENCY",
                details={"reason": "Missing username or subject in payload"}
            )
            raise credentials_exception
    except JWTError as e:
        audit_service.record_event(
            task_id="auth_event",
            user_id="anonymous",
            action="TOKEN_EXPIRED" if "expired" in str(e).lower() else "TOKEN_INVALID",
            component="AUTH_DEPENDENCY",
            details={"error": str(e)}
        )
        raise credentials_exception

    try:
        user_in_db = await UserRepository.get_by_username(db, username)
    except Exception as e:
        audit_service.record_event(
            task_id="auth_event",
            user_id=username,
            action="AUTH_SERVICE_UNAVAILABLE",
            component="AUTH_DEPENDENCY",
            details={"error": str(e)}
        )
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Authentication service temporarily unavailable."
        )

    if user_in_db is None or user_in_db.id != user_id:
        audit_service.record_event(
            task_id="auth_event",
            user_id=username,
            action="TOKEN_INVALID",
            component="AUTH_DEPENDENCY",
            details={"reason": "User record not found in PostgreSQL user store"}
        )
        raise credentials_exception

    if not user_in_db.is_active:
        audit_service.record_event(
            task_id="auth_event",
            user_id=username,
            action="ACCESS_DENIED",
            component="AUTH_DEPENDENCY",
            details={"reason": "User account is disabled/inactive in PostgreSQL"}
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive."
        )

    role_val = user_in_db.role.value if hasattr(user_in_db.role, "value") else str(user_in_db.role)
    created_ts = user_in_db.created_at if (hasattr(user_in_db, "created_at") and user_in_db.created_at is not None) else time.time()

    return User(
        id=user_in_db.id,
        username=user_in_db.username,
        role=UserRole(role_val),
        is_active=user_in_db.is_active,
        created_at=created_ts
    )

def require_roles(allowed_roles: List[Union[UserRole, str]]):
    normalized_allowed = [r.value if isinstance(r, UserRole) else str(r) for r in allowed_roles]

    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        user_role_str = current_user.role.value if hasattr(current_user.role, "value") else str(current_user.role)
        if user_role_str not in normalized_allowed:
            audit_service.record_event(
                task_id="rbac_event",
                user_id=current_user.username,
                action="ACCESS_DENIED",
                component="RBAC_DEPENDENCY",
                details={
                    "user_role": user_role_str,
                    "required_roles": normalized_allowed
                }
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: Required role in {normalized_allowed}, but user has role '{user_role_str}'."
            )
        return current_user

    return role_checker

def require_role(role: Union[UserRole, str]):
    return require_roles([role])
