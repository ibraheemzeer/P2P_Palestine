"""
Security utilities for P2P Palestine.
Includes encryption for sensitive data, password hashing, and JWT handling.
"""
import os
from datetime import datetime, timedelta
from typing import Optional, TYPE_CHECKING

from cryptography.fernet import Fernet
from jose import jwt
from passlib.context import CryptContext

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

# Security settings - should be loaded from environment variables
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Encryption key for sensitive data (bank details, wallet addresses)
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
fernet = Fernet(ENCRYPTION_KEY.encode())


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def encrypt_data(data: str) -> str:
    """Encrypt sensitive string data."""
    return fernet.encrypt(data.encode()).decode()


def decrypt_data(encrypted_data: str) -> str:
    """Decrypt sensitive string data."""
    return fernet.decrypt(encrypted_data.encode()).decode()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[dict]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except Exception:
        return None


async def log_audit_action(
    db: AsyncSession,
    user_id: int,
    action: str,
    details: str,
    entity_type: Optional[str] = None,
    entity_id: Optional[int] = None,
    old_values: Optional[dict] = None,
    new_values: Optional[dict] = None,
    ip_address: Optional[str] = None
):
    """
    Log an audit action to the database.
    This function creates immutable audit logs.
    """
    from app.models import AuditLog
    import json
    
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_values=json.dumps(old_values) if old_values else None,
        new_values=json.dumps(new_values) if new_values else None,
        ip_address=ip_address,
        details=details
    )
    
    db.add(audit_log)
    await db.flush()  # Ensure it's saved but don't commit yet
    return audit_log
