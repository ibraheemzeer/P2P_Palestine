"""
Database session management for P2P Palestine.
Uses AsyncEngine with asyncpg for asynchronous database operations.
"""
import os
from pydantic_settings import BaseSettings
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    DATABASE_URL: str = "postgresql://p2p_user:p2p_password@localhost:5432/p2p_palestine_db"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Cloudinary settings
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    # Additional settings from .env (optional)
    ENCRYPTION_KEY: str = "your-fernet-encryption-key-32-bytes-long!!"
    APP_NAME: str = "P2P Palestine"
    DEBUG: bool = True
    
    model_config = {
        "env_file": ".env",
        "case_sensitive": True,
        "extra": "ignore"  # Ignore extra fields in .env file
    }


# Global settings instance
_settings = None


def get_settings():
    """Get application settings (singleton pattern)."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


# Database URL - reads from environment variable for Docker compatibility
# Uses sqlite+aiosqlite for local development (no PostgreSQL driver needed)
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "sqlite+aiosqlite:///./p2p_local.db"
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
