"""
DEPRECATION NOTICE:
LocalUserStore was an in-memory user dictionary used exclusively during Phase 2 development.
In Phase 3 (PostgreSQL Persistence + Enterprise Data Layer), authoritative authentication,
user retrieval, and role management are handled directly by PostgreSQL via app.db.repositories.UserRepository.

This file is retained only for backwards compatibility with legacy tests if needed.
Production runtime authentication MUST NEVER call LocalUserStore.
"""

import logging
from typing import Dict, Optional
from app.auth.models import UserRole, UserInDB, User
from app.auth.security import hash_password, verify_password

logger = logging.getLogger("sovereign.auth.user_store")

class LocalUserStore:
    """
    [DEPRECATED] In-memory local user store.
    Superseded by PostgreSQL UserRepository.
    """

    def __init__(self):
        logger.warning("LocalUserStore initialized - DEPRECATED: PostgreSQL is authoritative in Phase 3.")
        self._users_by_username: Dict[str, UserInDB] = {}
        self._users_by_id: Dict[str, UserInDB] = {}

    def get_user_by_username(self, username: str) -> Optional[UserInDB]:
        return self._users_by_username.get(username.lower()) if username else None

    def get_user_by_id(self, user_id: str) -> Optional[UserInDB]:
        return self._users_by_id.get(user_id) if user_id else None

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user_in_db = self.get_user_by_username(username)
        if not user_in_db or not user_in_db.is_active:
            return None
        if verify_password(password, user_in_db.password_hash):
            return User(
                id=user_in_db.id,
                username=user_in_db.username,
                role=user_in_db.role,
                is_active=user_in_db.is_active,
                created_at=user_in_db.created_at
            )
        return None

user_store = LocalUserStore()
