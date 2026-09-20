import time
import uuid
from typing import Optional, List, Dict, Any
from sqlalchemy import select, update, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import UserModel, AuditEventModel, DocumentModel
from app.auth.models import UserRole

class UserRepository:
    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[UserModel]:
        if not username:
            return None
        stmt = select(UserModel).where(func.lower(UserModel.username) == username.lower())
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: str) -> Optional[UserModel]:
        if not user_id:
            return None
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str,
        password_hash: str,
        role: UserRole,
        is_active: bool = True,
        user_id: Optional[str] = None
    ) -> UserModel:
        new_id = user_id or f"usr_{uuid.uuid4().hex[:12]}"
        user = UserModel(
            id=new_id,
            username=username,
            password_hash=password_hash,
            role=role,
            is_active=is_active,
            created_at=time.time(),
            updated_at=time.time()
        )
        db.add(user)
        await db.flush()
        return user

    @staticmethod
    async def update_user(
        db: AsyncSession,
        user_id: str,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None
    ) -> Optional[UserModel]:
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            return None
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active
        user.updated_at = time.time()
        await db.flush()
        return user

    @staticmethod
    async def change_password(db: AsyncSession, user_id: str, new_password_hash: str) -> bool:
        user = await UserRepository.get_by_id(db, user_id)
        if not user:
            return False
        user.password_hash = new_password_hash
        user.updated_at = time.time()
        await db.flush()
        return True

    @staticmethod
    async def list_users(db: AsyncSession) -> List[UserModel]:
        stmt = select(UserModel).order_by(UserModel.username)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def count_active_admins(db: AsyncSession) -> int:
        stmt = select(func.count(UserModel.id)).where(
            UserModel.role == UserRole.ADMIN,
            UserModel.is_active == True
        )
        result = await db.execute(stmt)
        return result.scalar() or 0


class AuditRepository:
    @staticmethod
    async def record_event(
        db: AsyncSession,
        event_id: str,
        task_id: str,
        user_id: str,
        timestamp: float,
        action: str,
        component: str,
        details: Dict[str, Any],
        checksum: str
    ) -> AuditEventModel:
        event = AuditEventModel(
            event_id=event_id,
            task_id=task_id,
            user_id=user_id,
            timestamp=timestamp,
            action=action,
            component=component,
            details=details,
            checksum=checksum
        )
        db.add(event)
        await db.flush()
        return event

    @staticmethod
    async def get_events_by_task_id(db: AsyncSession, task_id: str) -> List[AuditEventModel]:
        stmt = select(AuditEventModel).where(AuditEventModel.task_id == task_id).order_by(AuditEventModel.timestamp)
        result = await db.execute(stmt)
        return list(result.scalars().all())


class DocumentRepository:
    @staticmethod
    async def create_document(
        db: AsyncSession,
        filename: str,
        file_type: str,
        uploaded_by: str,
        department: str,
        classification: str,
        status: str = "PENDING"
    ) -> DocumentModel:
        doc = DocumentModel(
            filename=filename,
            file_type=file_type,
            uploaded_by=uploaded_by,
            department=department,
            classification=classification,
            status=status,
            created_at=time.time(),
            updated_at=time.time()
        )
        db.add(doc)
        await db.flush()
        return doc

    @staticmethod
    async def update_status(db: AsyncSession, filename: str, status: str) -> Optional[DocumentModel]:
        stmt = select(DocumentModel).where(DocumentModel.filename == filename)
        result = await db.execute(stmt)
        doc = result.scalar_one_or_none()
        if doc:
            doc.status = status
            doc.updated_at = time.time()
            await db.flush()
        return doc

    @staticmethod
    async def get_by_filename(db: AsyncSession, filename: str) -> Optional[DocumentModel]:
        stmt = select(DocumentModel).where(DocumentModel.filename == filename)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def list_documents(db: AsyncSession) -> List[DocumentModel]:
        stmt = select(DocumentModel).order_by(DocumentModel.created_at.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())
