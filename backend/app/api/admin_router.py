import time
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User, UserRole
from app.auth.dependencies import require_roles
from app.auth.security import hash_password
from app.db.session import get_db
from app.db.repositories import UserRepository
from app.audit.audit_service import AuditService

router = APIRouter(prefix="/api/admin", tags=["Admin User Management"])
audit_service = AuditService()

class CreateUserRequest(BaseModel):
    username: str
    password: str
    role: UserRole

    model_config = ConfigDict(extra="forbid")

class UpdateUserRequest(BaseModel):
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None

    model_config = ConfigDict(extra="forbid")

@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user_endpoint(
    request: CreateUserRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    existing = await UserRepository.get_by_username(db, request.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{request.username}' already exists."
        )

    hashed = hash_password(request.password)
    user_db = await UserRepository.create_user(
        db=db,
        username=request.username,
        password_hash=hashed,
        role=request.role,
        is_active=True
    )

    role_val = request.role.value if hasattr(request.role, "value") else str(request.role)
    audit_service.record_event(
        task_id="admin_event",
        user_id=current_user.username,
        action="USER_CREATED",
        component="ADMIN_ROUTER",
        details={
            "created_username": user_db.username,
            "created_role": role_val,
            "created_user_id": user_db.id
        }
    )

    created_ts = user_db.created_at if (hasattr(user_db, "created_at") and user_db.created_at is not None) else time.time()
    return User(
        id=user_db.id,
        username=user_db.username,
        role=UserRole(role_val),
        is_active=user_db.is_active,
        created_at=created_ts
    )

@router.get("/users", response_model=List[User])
async def list_users_endpoint(
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    users_db = await UserRepository.list_users(db)
    return [
        User(
            id=u.id,
            username=u.username,
            role=UserRole(u.role.value if hasattr(u.role, "value") else str(u.role)),
            is_active=u.is_active,
            created_at=u.created_at if (hasattr(u, "created_at") and u.created_at is not None) else time.time()
        ) for u in users_db
    ]

@router.get("/users/{user_id}", response_model=User)
async def get_user_endpoint(
    user_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    user_db = await UserRepository.get_by_id(db, user_id)
    if not user_db:
        raise HTTPException(status_code=404, detail="User not found.")

    role_val = user_db.role.value if hasattr(user_db.role, "value") else str(user_db.role)
    created_ts = user_db.created_at if (hasattr(user_db, "created_at") and user_db.created_at is not None) else time.time()
    return User(
        id=user_db.id,
        username=user_db.username,
        role=UserRole(role_val),
        is_active=user_db.is_active,
        created_at=created_ts
    )

@router.patch("/users/{user_id}", response_model=User)
async def update_user_endpoint(
    user_id: str,
    request: UpdateUserRequest,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    target_user = await UserRepository.get_by_id(db, user_id)
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found.")

    if target_user.id == current_user.id and request.is_active is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-protection constraint: An administrator cannot deactivate their own active account."
        )

    if target_user.id == current_user.id and request.role is not None and request.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Self-protection constraint: An administrator cannot revoke their own ADMIN role."
        )

    target_role_str = target_user.role.value if hasattr(target_user.role, "value") else str(target_user.role)
    if target_role_str == "ADMIN":
        active_admins_count = await UserRepository.count_active_admins(db)
        is_deactivating = (request.is_active is False)
        is_demoting = (request.role is not None and request.role != UserRole.ADMIN)

        if (is_deactivating or is_demoting) and active_admins_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Self-protection constraint: Cannot deactivate or demote the last active ADMIN account."
            )

    updated_user = await UserRepository.update_user(
        db=db,
        user_id=user_id,
        role=request.role,
        is_active=request.is_active
    )

    role_val = updated_user.role.value if hasattr(updated_user.role, "value") else str(updated_user.role)
    audit_action = "USER_DEACTIVATED" if request.is_active is False else "USER_UPDATED"
    audit_service.record_event(
        task_id="admin_event",
        user_id=current_user.username,
        action=audit_action,
        component="ADMIN_ROUTER",
        details={
            "target_user_id": user_id,
            "target_username": updated_user.username,
            "new_role": role_val,
            "is_active": updated_user.is_active
        }
    )

    created_ts = updated_user.created_at if (hasattr(updated_user, "created_at") and updated_user.created_at is not None) else time.time()
    return User(
        id=updated_user.id,
        username=updated_user.username,
        role=UserRole(role_val),
        is_active=updated_user.is_active,
        created_at=created_ts
    )

@router.delete("/users/{user_id}")
async def deactivate_user_endpoint(
    user_id: str,
    current_user: User = Depends(require_roles([UserRole.ADMIN])),
    db: AsyncSession = Depends(get_db)
):
    return await update_user_endpoint(
        user_id=user_id,
        request=UpdateUserRequest(is_active=False),
        current_user=current_user,
        db=db
    )
