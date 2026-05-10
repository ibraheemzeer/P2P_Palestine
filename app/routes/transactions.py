"""
Transaction Routes for P2P Palestine Escrow System
Handles matching, locking, releasing, and dispute resolution
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_admin
from app.models import User, Order, Transaction, AuditLog, ExchangeRate
from app.schemas import (
    TransactionCreate, 
    TransactionResponse, 
    TransactionStatusUpdate,
    DisputeRequest
)
from app.core.commission_engine import calculate_commission
from app.core.security import log_audit_action
from datetime import datetime

router = APIRouter(prefix="/transactions", tags=["transactions"])


@router.post("/match/{order_id}", response_model=TransactionResponse)
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
        raise HTTPException(status_code=404, detail="Order not found")
    
    if order.status != "ACTIVE":
        raise HTTPException(status_code=400, detail=f"Order is not available. Status: {order.status}")
    
    if order.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot match your own order")
    
    # Determine buyer and seller
    if order.order_type == "BUY":
        buyer = current_user
        seller = order.user
    else:  # SELL
        seller = current_user
        buyer = order.user
    
    # Get current exchange rate
    rate_result = await db.execute(
        select(ExchangeRate).where(ExchangeRate.currency == order.currency)
    )
    exchange_rate_obj = rate_result.scalar_one_or_none()
    exchange_rate = exchange_rate_obj.rate if exchange_rate_obj else 1.0
    
    # Calculate commissions
    base_amount = order.amount  # Assuming order has amount field
    commission_calc = calculate_commission(base_amount, order.commission)
    
    # Create transaction within a database transaction for ACID compliance
    async with db.begin():
        # Update order status
        order.status = "LOCKED"
        
        # Create transaction record
        transaction = Transaction(
            buyer_id=buyer.id,
            seller_id=seller.id,
            order_id=order.id,
            amount=base_amount,
            currency=order.currency,
            blockchain_network=order.blockchain_network,
            exchange_rate=exchange_rate,
            buyer_pays=commission_calc["buyer_pays"],
            seller_receives=commission_calc["seller_receives"],
            platform_fee=commission_calc["platform_fee_total"],
            status="MATCHED"
        )
        
        db.add(transaction)
        await db.flush()  # Get transaction ID
        
        # Log audit
        await log_audit_action(
            db=db,
            user_id=current_user.id,
            action="TRANSACTION_MATCHED",
            details=f"Transaction {transaction.id} created from order {order_id}"
        )
    
    return transaction


@router.post("/{transaction_id}/lock", response_model=TransactionResponse)
async def lock_escrow(
    transaction_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin action: Lock escrow after confirming funds are received.
    Moves status from MATCHED to ESCROW_LOCKED.
    """
    async with db.begin():
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction.status != "MATCHED":
            raise HTTPException(
                status_code=400, 
                detail=f"Transaction must be in MATCHED status. Current: {transaction.status}"
            )
        
        transaction.status = "ESCROW_LOCKED"
        
        # Log audit
        await log_audit_action(
            db=db,
            user_id=current_user.id,
            action="ESCROW_LOCKED",
            details=f"Admin locked transaction {transaction_id}"
        )
    
    return transaction


@router.post("/{transaction_id}/release", response_model=TransactionResponse)
async def release_escrow(
    transaction_id: int,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin action: Release funds and complete the transaction.
    Moves status from ESCROW_LOCKED to COMPLETED.
    """
    async with db.begin():
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction.status != "ESCROW_LOCKED":
            raise HTTPException(
                status_code=400, 
                detail=f"Transaction must be in ESCROW_LOCKED status. Current: {transaction.status}"
            )
        
        transaction.status = "COMPLETED"
        transaction.completed_at = datetime.utcnow()
        
        # Log audit
        await log_audit_action(
            db=db,
            user_id=current_user.id,
            action="TRANSACTION_COMPLETED",
            details=f"Admin released funds for transaction {transaction_id}"
        )
    
    return transaction


@router.post("/{transaction_id}/dispute", response_model=TransactionResponse)
async def create_dispute(
    transaction_id: int,
    dispute_request: DisputeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    User or Admin action: Open a dispute for a transaction.
    Moves status to DISPUTED.
    """
    async with db.begin():
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction.status in ["COMPLETED", "DISPUTED"]:
            raise HTTPException(
                status_code=400, 
                detail=f"Cannot dispute transaction in {transaction.status} status"
            )
        
        transaction.status = "DISPUTED"
        transaction.dispute_reason = dispute_request.reason
        
        # Log audit
        await log_audit_action(
            db=db,
            user_id=current_user.id,
            action="DISPUTE_OPENED",
            details=f"Dispute opened for transaction {transaction_id}: {dispute_request.reason}"
        )
    
    return transaction


@router.post("/{transaction_id}/resolve", response_model=TransactionResponse)
async def resolve_dispute(
    transaction_id: int,
    dispute_request: DisputeRequest,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin action: Resolve a dispute by either completing or refunding.
    """
    async with db.begin():
        result = await db.execute(
            select(Transaction).where(Transaction.id == transaction_id)
        )
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        if transaction.status != "DISPUTED":
            raise HTTPException(
                status_code=400, 
                detail=f"Transaction is not in DISPUTED status. Current: {transaction.status}"
            )
        
        # Determine resolution based on request type
        if dispute_request.resolution == "COMPLETE":
            transaction.status = "COMPLETED"
            transaction.completed_at = datetime.utcnow()
            action = "DISPUTE_RESOLVED_COMPLETE"
        elif dispute_request.resolution == "REFUND":
            transaction.status = "REFUNDED"
            action = "DISPUTE_RESOLVED_REFUND"
        else:
            raise HTTPException(status_code=400, detail="Invalid resolution type")
        
        # Log audit
        await log_audit_action(
            db=db,
            user_id=current_user.id,
            action=action,
            details=f"Admin resolved dispute for transaction {transaction_id}"
        )
    
    return transaction


@router.get("/", response_model=List[TransactionResponse])
async def list_transactions(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List transactions. Admins see all, users see only their own.
    Implements anonymity for non-admin users.
    """
    query = select(Transaction)
    
    if not current_user.is_admin:
        # Regular users only see their own transactions
        query = query.where(
            (Transaction.buyer_id == current_user.id) | 
            (Transaction.seller_id == current_user.id)
        )
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return transactions
