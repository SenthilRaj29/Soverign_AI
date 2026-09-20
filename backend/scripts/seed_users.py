import sys
import os
import asyncio
import logging

# Ensure backend directory is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db.database import async_engine, Base, check_database_connection
from app.db.session import get_db_session_ctx
from app.db.repositories import UserRepository
from app.auth.models import UserRole
from app.auth.security import hash_password

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_users")

DEV_USERS = [
    {
        "user_id": "usr_eng_01",
        "username": "engineer",
        "env_var": "DEV_ENGINEER_PASSWORD",
        "default_pass": "Engineer@123",
        "role": UserRole.ENGINEER
    },
    {
        "user_id": "usr_mgr_01",
        "username": "manager",
        "env_var": "DEV_MANAGER_PASSWORD",
        "default_pass": "Manager@123",
        "role": UserRole.MANAGER
    },
    {
        "user_id": "usr_adm_01",
        "username": "admin",
        "env_var": "DEV_ADMIN_PASSWORD",
        "default_pass": "Admin@123",
        "role": UserRole.ADMIN
    },
]

async def seed_development_users():
    """
    Idempotent seeding script for development and test accounts in PostgreSQL.
    Creates tables if not existing, verifies user existence, and hashes passwords securely.
    """
    logger.info("Checking database connection for seeding...")
    is_connected = await check_database_connection()
    if not is_connected:
        logger.warning("Database unavailable. Creating tables on connected database if available...")

    # Ensure tables exist
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with get_db_session_ctx() as db:
        for user_info in DEV_USERS:
            username = user_info["username"]
            role = user_info["role"]
            raw_password = os.getenv(user_info["env_var"], user_info["default_pass"])

            existing_user = await UserRepository.get_by_username(db, username)
            if existing_user:
                logger.info(f"User '{username}' already exists (ID: {existing_user.id}, Role: {existing_user.role}). Skipping.")
            else:
                hashed = hash_password(raw_password)
                created = await UserRepository.create_user(
                    db=db,
                    username=username,
                    password_hash=hashed,
                    role=role,
                    is_active=True,
                    user_id=user_info["user_id"]
                )
                logger.info(f"Successfully seeded development user '{username}' (ID: {created.id}, Role: {created.role}).")

    logger.info("Database seeding process completed successfully.")

if __name__ == "__main__":
    asyncio.run(seed_development_users())
