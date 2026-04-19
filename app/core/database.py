"""
Database session management for P2P Palestine.
Uses AsyncEngine with asyncpg for asynchronous database operations.
"""
import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

# Database URL - reads from environment variable for Docker compatibility
# Uses postgresql+asyncpg driver for async support
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://p2p_user:p2p_password@localhost:5432/p2p_palestine_db"
)

# Convert to async URL if needed
if not SQLALCHEMY_DATABASE_URL.startswith("postgresql+asyncpg"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace(
        "postgresql://", "postgresql+asyncpg://"
    )

async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(
    class_=AsyncSession, 
    expire_on_commit=False, 
    bind=async_engine
)

Base = declarative_base()


async def get_db():
    """Dependency to get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (for development)."""
    from app.models import User, Order, Transaction, ExchangeRate, AuditLog
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
