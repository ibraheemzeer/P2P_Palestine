"""
Test suite for Immutable Audit Logs.
Verifies that AuditLog entries cannot be updated or deleted.
"""
import pytest
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import User, AuditLog, UserRole
from app.core.database import get_db, async_engine, Base
from app.core.security import get_password_hash


@pytest.fixture(scope="function")
async def test_db():
    """Create fresh database tables for each test."""
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(async_engine) as session:
        yield session
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def test_user(test_db):
    """Create a test user."""
    user = User(
        username="test_audit_user",
        email="audit@test.com",
        password_hash=get_password_hash("password123"),
        role=UserRole.USER
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.mark.asyncio
async def test_audit_log_creation(test_db, test_user):
    """Test that audit logs can be created successfully."""
    audit_log = AuditLog(
        user_id=test_user.id,
        action="TEST_ACTION",
        entity_type="Transaction",
        entity_id=1,
        details={"test": "data"},
        ip_address="127.0.0.1"
    )
    
    test_db.add(audit_log)
    await test_db.commit()
    await test_db.refresh(audit_log)
    
    assert audit_log.id is not None
    assert audit_log.action == "TEST_ACTION"
    assert audit_log.user_id == test_user.id


@pytest.mark.asyncio
async def test_audit_log_update_blocked(test_db, test_user):
    """Test that updating an audit log raises an exception."""
    # Create audit log
    audit_log = AuditLog(
        user_id=test_user.id,
        action="ORIGINAL_ACTION",
        entity_type="Transaction",
        entity_id=1
    )
    test_db.add(audit_log)
    await test_db.commit()
    await test_db.refresh(audit_log)
    
    # Try to update it
    audit_log.action = "MODIFIED_ACTION"
    
    # This should raise an exception due to immutable enforcement
    with pytest.raises(Exception) as exc_info:
        await test_db.commit()
    
    assert "IMMUTABLE VIOLATION" in str(exc_info.value)
    assert "cannot be updated" in str(exc_info.value)


@pytest.mark.asyncio
async def test_audit_log_delete_blocked(test_db, test_user):
    """Test that deleting an audit log raises an exception."""
    from sqlalchemy import delete
    
    # Create audit log
    audit_log = AuditLog(
        user_id=test_user.id,
        action="TO_DELETE",
        entity_type="Transaction",
        entity_id=1
    )
    test_db.add(audit_log)
    await test_db.commit()
    await test_db.refresh(audit_log)
    
    # Try to delete it
    stmt = delete(AuditLog).where(AuditLog.id == audit_log.id)
    
    # This should raise an exception due to immutable enforcement
    with pytest.raises(Exception) as exc_info:
        await test_db.execute(stmt)
        await test_db.commit()
    
    assert "IMMUTABLE VIOLATION" in str(exc_info.value)
    assert "cannot be deleted" in str(exc_info.value)


@pytest.mark.asyncio
async def test_audit_log_read_allowed(test_db, test_user):
    """Test that reading audit logs works normally."""
    # Create audit log
    audit_log = AuditLog(
        user_id=test_user.id,
        action="READ_TEST",
        entity_type="Transaction",
        entity_id=999
    )
    test_db.add(audit_log)
    await test_db.commit()
    
    # Read it back
    result = await test_db.execute(
        select(AuditLog).where(AuditLog.user_id == test_user.id)
    )
    logs = result.scalars().all()
    
    assert len(logs) >= 1
    assert any(log.action == "READ_TEST" for log in logs)


@pytest.mark.asyncio
async def test_multiple_audit_logs_append_only(test_db, test_user):
    """Test that multiple audit logs can be appended but not modified."""
    # Create multiple logs
    for i in range(5):
        log = AuditLog(
            user_id=test_user.id,
            action=f"ACTION_{i}",
            entity_type="Transaction",
            entity_id=i
        )
        test_db.add(log)
    
    await test_db.commit()
    
    # Verify all were created
    result = await test_db.execute(
        select(func.count()).select_from(AuditLog).where(AuditLog.user_id == test_user.id)
    )
    count = result.scalar()
    assert count == 5
    
    # Try to modify one
    result = await test_db.execute(
        select(AuditLog).where(AuditLog.action == "ACTION_0")
    )
    first_log = result.scalar_one()
    first_log.action = "MODIFIED"
    
    # Should fail on commit
    with pytest.raises(Exception) as exc_info:
        await test_db.commit()
    
    assert "IMMUTABLE VIOLATION" in str(exc_info.value)
