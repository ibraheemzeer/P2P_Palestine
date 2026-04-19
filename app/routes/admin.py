"""
Admin Routes for P2P Palestine
Handles exchange rate updates and admin dashboard operations
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.database import get_db
from app.core.auth import get_current_admin
from app.models import User, ExchangeRate, Transaction, Order, AuditLog
from app.schemas.exchange_rate import ExchangeRateCreate, ExchangeRateResponse
from app.core.security import log_audit_action
from datetime import datetime

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/exchange-rates/", response_model=ExchangeRateResponse)
async def update_exchange_rate(
    rate_data: ExchangeRateCreate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin action: Update daily exchange rate for a currency.
    """
    async with db.begin():
        # Check if rate exists
        result = await db.execute(
            select(ExchangeRate).where(ExchangeRate.currency == rate_data.currency)
        )
        existing_rate = result.scalar_one_or_none()
        
        if existing_rate:
            existing_rate.rate = rate_data.rate
            existing_rate.updated_at = datetime.utcnow()
            rate_obj = existing_rate
            action = "EXCHANGE_RATE_UPDATED"
        else:
            rate_obj = ExchangeRate(
                currency=rate_data.currency,
                rate=rate_data.rate,
                updated_by=current_user.id
            )
            db.add(rate_obj)
            await db.flush()
            action = "EXCHANGE_RATE_CREATED"
        
        # Log audit
        await log_audit_action(
            db=db,
            user_id=current_user.id,
            action=action,
            details=f"Exchange rate for {rate_data.currency} set to {rate_data.rate}"
        )
    
    return rate_obj


@router.get("/dashboard/stats")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin dashboard: Get platform statistics.
    """
    # Count users
    user_count = await db.execute(select(User))
    total_users = len(user_count.scalars().all())
    
    # Count active orders
    active_orders = await db.execute(
        select(Order).where(Order.status == "ACTIVE")
    )
    total_active_orders = len(active_orders.scalars().all())
    
    # Count transactions by status
    matched = await db.execute(select(Transaction).where(Transaction.status == "MATCHED"))
    locked = await db.execute(select(Transaction).where(Transaction.status == "ESCROW_LOCKED"))
    completed = await db.execute(select(Transaction).where(Transaction.status == "COMPLETED"))
    disputed = await db.execute(select(Transaction).where(Transaction.status == "DISPUTED"))
    
    stats = {
        "total_users": total_users,
        "active_orders": total_active_orders,
        "transactions": {
            "matched": len(matched.scalars().all()),
            "locked": len(locked.scalars().all()),
            "completed": len(completed.scalars().all()),
            "disputed": len(disputed.scalars().all())
        }
    }
    
    return stats


@router.get("/audit-logs/", response_model=List[dict])
async def list_audit_logs(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin action: View immutable audit logs.
    Read-only access.
    """
    query = select(AuditLog).order_by(AuditLog.created_at.desc())
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs
