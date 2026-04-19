"""
Transaction routes for P2P Palestine.
Handles escrow matching, locking, releasing, and dispute resolution.
All financial operations are wrapped in database transactions for ACID compliance.
"""
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_admin
from app.core.commission_engine import calculate_commission
from app.models import User, Order, Transaction, ExchangeRate, AuditLog, OrderStatus, TransactionStatus, UserRole
from app.schemas import (
    TransactionCreate, 
    TransactionResponse, 
    TransactionLockRequest,
    TransactionReleaseRequest,
    DisputeRequest,
    ExchangeRateCreate,
    ExchangeRateResponse,
    AuditLogResponse
)

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/match/{order_id}", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def match_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Match an existing order to create a transaction.
    Changes order status to LOCKED and calculates commissions.
    """
    # Fetch the order
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    
    if order.status != OrderStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Order is not active. Current status: {order.status}"
        )
    
    if order.creator_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot match your own order"
        )
    
    # Determine roles
    if order.order_type == "BUY":
        # User matching a BUY order is the SELLER
        seller = current_user
        buyer = await db.get(User, order.creator_id)
    else:
        # User matching a SELL order is the BUYER
        buyer = current_user
        seller = await db.get(User, order.creator_id)
    
    if not buyer or not seller:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Get exchange rate
    result = await db.execute(
        select(ExchangeRate).where(ExchangeRate.currency == order.currency)
    )
    exchange_rate_obj = result.scalar_one_or_none()
    exchange_rate = exchange_rate_obj.rate if exchange_rate_obj else 1.0
    
    # Calculate commissions
    base_amount = order.amount  # Assuming this is the base amount in USDT
    commission_calc = calculate_commission(base_amount, order.commission)
    
    # Create transaction
    transaction = Transaction(
        order_id=order.id,
        buyer_id=buyer.id,
        seller_id=seller.id,
        amount=base_amount,
        currency=order.currency,
        exchange_rate=exchange_rate,
        seller_commission=order.commission,
        platform_fee_buyer=commission_calc.platform_fee_buyer,
        platform_fee_seller=commission_calc.platform_fee_seller,
        buyer_pays=commission_calc.buyer_pays,
        seller_receives=commission_calc.seller_receives,
        status=TransactionStatus.MATCHED,
        blockchain_network=order.blockchain_network
    )
    
    # Update order status
    order.status = OrderStatus.LOCKED
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="MATCH_ORDER",
        details={
            "order_id": order.id,
            "transaction_amount": base_amount,
            "buyer_id": buyer.id,
            "seller_id": seller.id
        }
    )
    
    async with db.begin():
        db.add(transaction)
        db.add(audit_log)
        # Order status update is tracked automatically
    
    await db.refresh(transaction)
    return transaction


@router.post("/{transaction_id}/lock", response_model=TransactionResponse)
async def lock_transaction(
    transaction_id: int,
    request: TransactionLockRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin action: Lock escrow after confirming funds are received.
    Moves transaction from MATCHED to ESCROW_LOCKED.
    """
    transaction = await db.get(Transaction, transaction_id)
    
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    
    if transaction.status != TransactionStatus.MATCHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction is not in MATCHED status. Current: {transaction.status}"
        )
    
    # Update status
    old_status = transaction.status
    transaction.status = TransactionStatus.ESCROW_LOCKED
    transaction.locked_at = datetime.now(timezone.utc)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="LOCK_ESCROW",
        details={
            "transaction_id": transaction_id,
            "old_status": old_status.value,
            "new_status": transaction.status.value,
            "confirmed_by_admin": current_admin.username
        }
    )
    
    async with db.begin():
        db.add(audit_log)
    
    await db.refresh(transaction)
    return transaction


@router.post("/{transaction_id}/release", response_model=TransactionResponse)
async def release_transaction(
    transaction_id: int,
    request: TransactionReleaseRequest,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin action: Release funds and complete the transaction.
    Moves transaction from ESCROW_LOCKED to COMPLETED.
    """
    transaction = await db.get(Transaction, transaction_id)
    
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    
    if transaction.status != TransactionStatus.ESCROW_LOCKED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction is not locked. Current: {transaction.status}"
        )
    
    # Update status
    old_status = transaction.status
    transaction.status = TransactionStatus.COMPLETED
    transaction.completed_at = datetime.now(timezone.utc)
    
    # Update order status
    order = await db.get(Order, transaction.order_id)
    if order:
        order.status = OrderStatus.COMPLETED
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="RELEASE_FUNDS",
        details={
            "transaction_id": transaction_id,
            "old_status": old_status.value,
            "new_status": transaction.status.value,
            "released_by_admin": current_admin.username,
            "buyer_received": transaction.seller_receives,
            "platform_fee_total": transaction.platform_fee_buyer + transaction.platform_fee_seller
        }
    )
    
    async with db.begin():
        db.add(audit_log)
    
    await db.refresh(transaction)
    return transaction


@router.post("/{transaction_id}/dispute", response_model=TransactionResponse)
async def create_dispute(
    transaction_id: int,
    request: DisputeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a dispute on a transaction.
    Can be initiated by buyer or seller, or admin.
    """
    transaction = await db.get(Transaction, transaction_id)
    
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    
    if transaction.status in [TransactionStatus.COMPLETED, TransactionStatus.DISPUTED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot dispute transaction in {transaction.status} status"
        )
    
    # Check if user is involved in transaction
    if current_user.id not in [transaction.buyer_id, transaction.seller_id]:
        # Only admin can dispute without being involved
        if current_user.role != UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only involved parties or admin can create disputes"
            )
    
    # Update status
    old_status = transaction.status
    transaction.status = TransactionStatus.DISPUTED
    transaction.dispute_reason = request.reason
    transaction.disputed_at = datetime.now(timezone.utc)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_user.id,
        action="CREATE_DISPUTE",
        details={
            "transaction_id": transaction_id,
            "old_status": old_status.value,
            "new_status": transaction.status.value,
            "reason": request.reason,
            "initiated_by": current_user.username
        }
    )
    
    async with db.begin():
        db.add(audit_log)
    
    await db.refresh(transaction)
    return transaction


@router.post("/{transaction_id}/resolve", response_model=TransactionResponse)
async def resolve_dispute(
    transaction_id: int,
    request: DisputeRequest,
    action: str,  # "refund" or "complete"
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin action: Resolve a dispute by either refunding or completing the transaction.
    """
    transaction = await db.get(Transaction, transaction_id)
    
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    
    if transaction.status != TransactionStatus.DISPUTED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Transaction is not in dispute. Current: {transaction.status}"
        )
    
    if action not in ["refund", "complete"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Action must be 'refund' or 'complete'"
        )
    
    # Update status based on action
    old_status = transaction.status
    if action == "refund":
        transaction.status = TransactionStatus.REFUNDED
        # Refund logic would go here (return funds to buyer)
    else:  # complete
        transaction.status = TransactionStatus.COMPLETED
        transaction.completed_at = datetime.now(timezone.utc)
        # Update order status
        order = await db.get(Order, transaction.order_id)
        if order:
            order.status = OrderStatus.COMPLETED
    
    transaction.dispute_resolution = request.reason
    transaction.resolved_at = datetime.now(timezone.utc)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="RESOLVE_DISPUTE",
        details={
            "transaction_id": transaction_id,
            "old_status": old_status.value,
            "new_status": transaction.status.value,
            "action_taken": action,
            "resolution": request.reason,
            "resolved_by": current_admin.username
        }
    )
    
    async with db.begin():
        db.add(audit_log)
    
    await db.refresh(transaction)
    return transaction


# Admin Exchange Rate Management
@router.post("/admin/exchange-rates", response_model=ExchangeRateResponse, status_code=status.HTTP_201_CREATED)
async def update_exchange_rate(
    rate_data: ExchangeRateCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin action: Update daily exchange rate for a currency.
    """
    # Check if rate exists
    result = await db.execute(
        select(ExchangeRate).where(ExchangeRate.currency == rate_data.currency)
    )
    existing_rate = result.scalar_one_or_none()
    
    if existing_rate:
        existing_rate.rate = rate_data.rate
        existing_rate.updated_by = current_admin.id
        existing_rate.updated_at = datetime.now(timezone.utc)
        rate_obj = existing_rate
    else:
        rate_obj = ExchangeRate(
            currency=rate_data.currency,
            rate=rate_data.rate,
            updated_by=current_admin.id
        )
        db.add(rate_obj)
    
    # Create audit log
    audit_log = AuditLog(
        user_id=current_admin.id,
        action="UPDATE_EXCHANGE_RATE",
        details={
            "currency": rate_data.currency,
            "new_rate": rate_data.rate,
            "updated_by": current_admin.username
        }
    )
    
    async with db.begin():
        db.add(audit_log)
    
    await db.refresh(rate_obj)
    return rate_obj


@router.get("/admin/exchange-rates", response_model=List[ExchangeRateResponse])
async def get_all_exchange_rates(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin action: Get all current exchange rates.
    """
    result = await db.execute(select(ExchangeRate))
    rates = result.scalars().all()
    return rates


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific transaction by ID.
    Regular users can only see transactions they're involved in.
    Admins can see all transactions.
    """
    transaction = await db.get(Transaction, transaction_id)
    
    if not transaction:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found")
    
    # Check permissions
    if current_user.role != UserRole.ADMIN:
        if current_user.id not in [transaction.buyer_id, transaction.seller_id]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only view your own transactions"
            )
    
    return transaction


@router.get("", response_model=List[TransactionResponse])
async def get_user_transactions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all transactions for the current user.
    Admins see all transactions, regular users see only their own.
    """
    if current_user.role == UserRole.ADMIN:
        result = await db.execute(select(Transaction))
    else:
        result = await db.execute(
            select(Transaction).where(
                (Transaction.buyer_id == current_user.id) | 
                (Transaction.seller_id == current_user.id)
            )
        )
    
    transactions = result.scalars().all()
    return transactions
