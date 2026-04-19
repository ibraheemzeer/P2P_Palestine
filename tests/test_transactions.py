"""
Tests for Transaction Escrow flow.
Covers the complete lifecycle: Match -> Lock -> Release/Dispute.
"""
import pytest
from decimal import Decimal
from sqlalchemy import select
from app.models import Transaction, Order, User, UserRole
from app.core.security import get_password_hash


@pytest.mark.asyncio
async def test_transaction_create(db_session):
    """Test creating a transaction."""
    # Create users
    buyer = User(
        username="buyer_test",
        email="buyer@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    seller = User(
        username="seller_test",
        email="seller@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    db_session.add(buyer)
    db_session.add(seller)
    await db_session.commit()
    
    # Create transaction
    transaction = Transaction(
        buyer_id=buyer.id,
        seller_id=seller.id,
        amount=Decimal("100.00"),
        currency="USD",
        blockchain_network="TRX",
        exchange_rate=Decimal("1.0"),
        buyer_pays=Decimal("100.75"),
        seller_receives=Decimal("99.25"),
        platform_fee=Decimal("1.50"),
        status="MATCHED"
    )
    
    db_session.add(transaction)
    await db_session.commit()
    await db_session.refresh(transaction)
    
    assert transaction.id is not None
    assert transaction.status == "MATCHED"
    assert transaction.buyer_id == buyer.id
    assert transaction.seller_id == seller.id


@pytest.mark.asyncio
async def test_transaction_lock_escrow(db_session):
    """Test locking escrow (MATCHED -> ESCROW_LOCKED)."""
    # Setup users and transaction
    buyer = User(username="buyer1", email="b1@test.com", hashed_password="hash", role=UserRole.USER)
    seller = User(username="seller1", email="s1@test.com", hashed_password="hash", role=UserRole.USER)
    db_session.add_all([buyer, seller])
    await db_session.commit()
    
    transaction = Transaction(
        buyer_id=buyer.id,
        seller_id=seller.id,
        amount=Decimal("100.00"),
        status="MATCHED"
    )
    db_session.add(transaction)
    await db_session.commit()
    
    # Lock the escrow
    transaction.status = "ESCROW_LOCKED"
    await db_session.commit()
    await db_session.refresh(transaction)
    
    assert transaction.status == "ESCROW_LOCKED"


@pytest.mark.asyncio
async def test_transaction_release_funds(db_session):
    """Test releasing funds (ESCROW_LOCKED -> COMPLETED)."""
    # Setup
    buyer = User(username="buyer2", email="b2@test.com", hashed_password="hash", role=UserRole.USER)
    seller = User(username="seller2", email="s2@test.com", hashed_password="hash", role=UserRole.USER)
    db_session.add_all([buyer, seller])
    await db_session.commit()
    
    transaction = Transaction(
        buyer_id=buyer.id,
        seller_id=seller.id,
        amount=Decimal("100.00"),
        status="ESCROW_LOCKED"
    )
    db_session.add(transaction)
    await db_session.commit()
    
    # Release funds
    transaction.status = "COMPLETED"
    await db_session.commit()
    await db_session.refresh(transaction)
    
    assert transaction.status == "COMPLETED"
    assert transaction.completed_at is not None


@pytest.mark.asyncio
async def test_transaction_dispute(db_session):
    """Test opening a dispute."""
    # Setup
    buyer = User(username="buyer3", email="b3@test.com", hashed_password="hash", role=UserRole.USER)
    seller = User(username="seller3", email="s3@test.com", hashed_password="hash", role=UserRole.USER)
    db_session.add_all([buyer, seller])
    await db_session.commit()
    
    transaction = Transaction(
        buyer_id=buyer.id,
        seller_id=seller.id,
        amount=Decimal("100.00"),
        status="ESCROW_LOCKED",
        dispute_reason=None
    )
    db_session.add(transaction)
    await db_session.commit()
    
    # Open dispute
    transaction.status = "DISPUTED"
    transaction.dispute_reason = "Buyer claims non-delivery"
    await db_session.commit()
    await db_session.refresh(transaction)
    
    assert transaction.status == "DISPUTED"
    assert transaction.dispute_reason == "Buyer claims non-delivery"


@pytest.mark.asyncio
async def test_transaction_resolve_dispute_complete(db_session):
    """Test resolving dispute by completing transaction."""
    # Setup
    buyer = User(username="buyer4", email="b4@test.com", hashed_password="hash", role=UserRole.USER)
    seller = User(username="seller4", email="s4@test.com", hashed_password="hash", role=UserRole.USER)
    db_session.add_all([buyer, seller])
    await db_session.commit()
    
    transaction = Transaction(
        buyer_id=buyer.id,
        seller_id=seller.id,
        amount=Decimal("100.00"),
        status="DISPUTED"
    )
    db_session.add(transaction)
    await db_session.commit()
    
    # Resolve by completing
    transaction.status = "COMPLETED"
    await db_session.commit()
    await db_session.refresh(transaction)
    
    assert transaction.status == "COMPLETED"


@pytest.mark.asyncio
async def test_transaction_resolve_dispute_refund(db_session):
    """Test resolving dispute by refunding."""
    # Setup
    buyer = User(username="buyer5", email="b5@test.com", hashed_password="hash", role=UserRole.USER)
    seller = User(username="seller5", email="s5@test.com", hashed_password="hash", role=UserRole.USER)
    db_session.add_all([buyer, seller])
    await db_session.commit()
    
    transaction = Transaction(
        buyer_id=buyer.id,
        seller_id=seller.id,
        amount=Decimal("100.00"),
        status="DISPUTED"
    )
    db_session.add(transaction)
    await db_session.commit()
    
    # Resolve by refunding
    transaction.status = "REFUNDED"
    await db_session.commit()
    await db_session.refresh(transaction)
    
    assert transaction.status == "REFUNDED"
