"""
Routes for Order Management
Handles creating, listing, and viewing orders with anonymity.
"""
from typing import List
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.core.auth import get_current_user, get_current_admin
from app.services.cloudinary_service import upload_proof_of_funds
from app.models import User, Order, OrderType, OrderStatus, Currency, BlockchainNetwork, UserRole
from app.schemas import OrderCreate, OrderResponse, OrderAdminResponse, PaginationParams

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse)
async def create_order(
    order_data: OrderCreate,
    proof_of_funds: UploadFile = File(..., description="Proof of Funds image"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new BUY or SELL order.
    Requires uploading a Proof of Funds image.
    Initial status is PENDING until admin approval.
    """
    # Upload proof of funds to Cloudinary
    proof_url = await upload_proof_of_funds(proof_of_funds, current_user.id)
    
    # Create order
    new_order = Order(
        order_type=order_data.order_type,
        min_amount=order_data.min_amount,
        max_amount=order_data.max_amount,
        commission=order_data.commission,
        currency=order_data.currency,
        blockchain_network=order_data.blockchain_network,
        status=OrderStatus.PENDING,  # Start as PENDING for admin review
        creator_id=current_user.id,
        rejection_reason=None
    )
    
    # Note: In real implementation, you might store proof_url in a separate field
    # For now, we'll assume it's stored elsewhere or in a related table
    
    db.add(new_order)
    await db.commit()
    await db.refresh(new_order)
    
    # Return with masked identity
    return {
        **new_order.__dict__,
        "creator_masked_identity": current_user.get_masked_identity()
    }


@router.get("/", response_model=List[OrderResponse])
async def get_orders(
    order_type: OrderType = None,
    currency: Currency = None,
    status_filter: OrderStatus = None,
    pagination: PaginationParams = Depends(),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all active orders.
    Non-admin users see masked identities (anonymous mode).
    Admin users see real usernames.
    """
    query = select(Order)
    
    # Apply filters
    if order_type:
        query = query.where(Order.order_type == order_type)
    if currency:
        query = query.where(Order.currency == currency)
    if status_filter:
        query = query.where(Order.status == status_filter)
    else:
        # Default to showing only ACTIVE orders for regular users
        if current_user.role != UserRole.ADMIN:
            query = query.where(Order.status == OrderStatus.ACTIVE)
    
    # Apply pagination
    query = query.offset(pagination.skip).limit(pagination.limit)
    
    result = await db.execute(query)
    orders = result.scalars().all()
    
    # Convert to response with masked identities for non-admins
    is_admin = current_user.role == UserRole.ADMIN
    response_list = []
    
    for order in orders:
        order_dict = {**order.__dict__}
        
        if is_admin:
            # Admin sees real username
            order_dict["creator_username"] = order.creator.username
            order_dict["creator_masked_identity"] = order.creator.username
        else:
            # Regular user sees masked identity
            order_dict["creator_masked_identity"] = order.creator.get_masked_identity()
        
        response_list.append(order_dict)
    
    return response_list


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order(
    order_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific order by ID.
    Shows masked identity for non-admin users.
    """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Check permissions - only allow viewing if:
    # 1. User is admin, OR
    # 2. User is the creator, OR
    # 3. Order is ACTIVE (public)
    is_admin = current_user.role == UserRole.ADMIN
    if not (is_admin or order.creator_id == current_user.id or order.status == OrderStatus.ACTIVE):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this order"
        )
    
    order_dict = {**order.__dict__}
    
    if is_admin:
        order_dict["creator_username"] = order.creator.username
    else:
        order_dict["creator_masked_identity"] = order.creator.get_masked_identity()
    
    return order_dict


@router.put("/{order_id}/status", response_model=OrderAdminResponse)
async def update_order_status(
    order_id: int,
    new_status: OrderStatus,
    rejection_reason: str = None,
    current_user: User = Depends(get_current_admin),  # Admin only
    db: AsyncSession = Depends(get_db)
):
    """
    Update order status (Admin only).
    Used to approve (PENDING -> ACTIVE) or reject (PENDING -> REJECTED) orders.
    """
    result = await db.execute(select(Order).where(Order.id == order_id))
    order = result.scalar_one_or_none()
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found"
        )
    
    # Update status
    order.status = new_status
    
    if new_status == OrderStatus.REJECTED and rejection_reason:
        order.rejection_reason = rejection_reason
    elif new_status == OrderStatus.ACTIVE:
        order.rejection_reason = None  # Clear rejection reason if approved
    
    await db.commit()
    await db.refresh(order)
    
    return {
        **order.__dict__,
        "creator_username": order.creator.username
    }
