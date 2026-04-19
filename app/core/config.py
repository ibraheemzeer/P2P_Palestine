"""
Pydantic configuration and settings for P2P Palestine.
Loads environment variables using Pydantic v2 Settings.
"""
import os
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Database
    DATABASE_URL: str = "postgresql://p2p_user:p2p_password@localhost:5432/p2p_palestine_db"
    
    # Security
    SECRET_KEY: str = "your-super-secret-key-change-in-production-min-32-chars"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Encryption (Fernet key for sensitive data)
    ENCRYPTION_KEY: str = "your-fernet-encryption-key-32-bytes-long!!"
    
    # Cloudinary Configuration
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    
    # Application Settings
    APP_NAME: str = "P2P Palestine"
    DEBUG: bool = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


# Global settings instance for easy import
settings = get_settings()


# Pydantic v2 configuration for models
class BaseConfig:
    """Base configuration for all Pydantic models."""
    from_attributes = True
    populate_by_name = True
