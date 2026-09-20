import os
import asyncio
import logging
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

# Ensure environment variables are loaded
load_dotenv()

logger = logging.getLogger("sovereign.db")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://sovereign:sovereign_pass@localhost:5432/sovereign_db"
)

if DATABASE_URL.startswith("postgresql://"):
    ASYNC_DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://", 1)
else:
    ASYNC_DATABASE_URL = DATABASE_URL

# Async Engine with short connection timeout
async_engine = create_async_engine(
    ASYNC_DATABASE_URL,
    echo=False,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=1800,
    connect_args={"timeout": 2.0}
)

# Async Session Factory
async_session_factory = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

class Base(DeclarativeBase):
    pass

async def check_database_connection(timeout_seconds: float = 2.0) -> bool:
    """
    Verifies actual connectivity to PostgreSQL database with a strict timeout.
    Returns True if healthy, False if connection fails or times out.
    """
    try:
        async with asyncio.timeout(timeout_seconds):
            async with async_engine.connect() as conn:
                result = await conn.execute(text("SELECT 1"))
                return result.scalar() == 1
    except Exception as e:
        logger.warning(f"Database connection check failed: {e}")
        return False
