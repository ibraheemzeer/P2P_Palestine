"""
Pydantic schemas for P2P Palestine.
Defines request/response models for API endpoints.
"""
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from pydantic import BaseModel, Field, EmailStr, field_validator, ConfigDict

from app.models import UserRole, OrderType, OrderStatus, TransactionStatus, Currency, BlockchainNetwork


# =============================================================================
# User Schemas
# =============================================================================

class UserBase(BaseModel):
    """Base user schema."""
    model_config = ConfigDict(from_attributes=True)
    
    username: str = Field(..., min_length=3, max_length=50, pattern="^[a-zA-Z0-9_]+$")
    email: EmailStr
    public_display_name: Optional[str] = Field(None, max_length=50)


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating user information."""
    model_config = ConfigDict(from_attributes=True)
    
    public_display_name: Optional[str] = Field(None, max_length=50)
    bank_details: Optional[str] = None  # Will be encrypted before storing
    wallet_addresses: Optional[str] = None  # Will be encrypted before storing


class UserResponse(UserBase):
    """Schema for user response (public view)."""
    id: int
    role: UserRole
    is_verified: bool
    created_at: datetime
    
    # Masked identity for privacy
    masked_identity: str
    
    class Config:
        from_attributes = True


class UserAdminResponse(UserBase):
    """Schema for user response (admin view - full details)."""
    id: int
    role: UserRole
    is_active: bool
    is_verified: bool
    bank_details_decrypted: Optional[str] = None
    wallet_addresses_decrypted: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# Authentication Schemas
# =============================================================================

class Token(BaseModel):
    """JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Decoded token data."""
    username: Optional[str] = None
    user_id: Optional[int] = None
    role: Optional[UserRole] = None


class LoginRequest(BaseModel):
    """Login request schema."""
    username: str
    password: str


# =============================================================================
# Exchange Rate Schemas
# =============================================================================

class ExchangeRateBase(BaseModel):
    """Base exchange rate schema."""
    model_config = ConfigDict(from_attributes=True)
    
    target_currency: Currency
    rate: Decimal = Field(..., gt=0, decimal_places=6)


class ExchangeRateCreate(ExchangeRateBase):
    """Schema for creating/updating exchange rate."""
    base_currency: str = "USD"


class ExchangeRateResponse(ExchangeRateBase):
    """Schema for exchange rate response."""
    id: int
    base_currency: str
    updated_by: int
    created_at: datetime
    is_active: bool
    
    class Config:
        from_attributes = True


# =============================================================================
# Order Schemas
# =============================================================================

class OrderBase(BaseModel):
    """Base order schema."""
    model_config = ConfigDict(from_attributes=True)
    
    order_type: OrderType
    min_amount: Decimal = Field(..., gt=0, decimal_places=2)
    max_amount: Decimal = Field(..., gt=0, decimal_places=2)
    commission: Decimal = Field(..., ge=0, le=0.035, decimal_places=4)  # 0% - 3.5%
    currency: Currency
    blockchain_network: BlockchainNetwork
    
    @field_validator('max_amount')
    @classmethod
    def validate_amount_range(cls, v, info):
        if 'min_amount' in info.data and v <= info.data['min_amount']:
            raise ValueError('max_amount must be greater than min_amount')
        return v


class OrderCreate(OrderBase):
    """Schema for creating a new order."""
    pass


class OrderUpdate(BaseModel):
    """Schema for updating an order."""
    model_config = ConfigDict(from_attributes=True)
    
    status: Optional[OrderStatus] = None
    rejection_reason: Optional[str] = None
    min_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    max_amount: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    commission: Optional[Decimal] = Field(None, ge=0, le=0.035, decimal_places=4)


class OrderResponse(OrderBase):
    """Schema for order response."""
    id: int
    status: OrderStatus
    creator_id: int
    creator_masked_identity: str  # Anonymous identity
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class OrderAdminResponse(OrderBase):
    """Schema for order response (admin view)."""
    id: int
    status: OrderStatus
    creator_id: int
    creator_username: str  # Real username visible to admin
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# Transaction Schemas
# =============================================================================

class TransactionBase(BaseModel):
    """Base transaction schema."""
    model_config = ConfigDict(from_attributes=True)
    
    base_amount: Decimal = Field(..., gt=0, decimal_places=2)


class TransactionCreate(TransactionBase):
    """Schema for creating a transaction (accepting an order)."""
    order_id: int


class TransactionUpdate(BaseModel):
    """Schema for updating transaction status."""
    model_config = ConfigDict(from_attributes=True)
    
    status: Optional[TransactionStatus] = None
    payment_proof_url: Optional[str] = None
    payment_reference: Optional[str] = None
    dispute_reason: Optional[str] = None


class TransactionResponse(TransactionBase):
    """Schema for transaction response."""
    id: int
    order_id: int
    initiator_id: int
    counterparty_id: int
    initiator_masked_identity: str
    counterparty_masked_identity: str
    buyer_pays: Decimal
    seller_receives: Decimal
    platform_fee: Decimal
    status: TransactionStatus
    payment_proof_url: Optional[str] = None
    payment_reference: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class TransactionAdminResponse(TransactionBase):
    """Schema for transaction response (admin view)."""
    id: int
    order_id: int
    initiator_id: int
    counterparty_id: int
    initiator_username: str
    counterparty_username: str
    buyer_pays: Decimal
    seller_receives: Decimal
    platform_fee: Decimal
    status: TransactionStatus
    payment_proof_url: Optional[str] = None
    payment_reference: Optional[str] = None
    dispute_reason: Optional[str] = None
    resolved_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# =============================================================================
# Commission Calculation Schemas
# =============================================================================

class CommissionCalculation(BaseModel):
    """Schema for commission calculation result."""
    base_amount: Decimal
    seller_commission: Decimal  # Seller's commission (0% - 3.5%)
    platform_fee: Decimal  # Fixed 0.75% per side
    buyer_pays: Decimal  # Base * (1 + Seller_Commission + 0.0075)
    seller_receives: Decimal  # Base * (1 + Seller_Commission - 0.0075)
    total_platform_profit: Decimal  # 1.5% total


# =============================================================================
# Audit Log Schemas
# =============================================================================

class AuditLogBase(BaseModel):
    """Base audit log schema."""
    model_config = ConfigDict(from_attributes=True)
    
    action: str
    entity_type: str
    entity_id: Optional[int] = None


class AuditLogResponse(AuditLogBase):
    """Schema for audit log response."""
    id: int
    user_id: Optional[int] = None
    old_values: Optional[str] = None
    new_values: Optional[str] = None
    ip_address: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


# =============================================================================
# File Upload Schemas (Cloudinary)
# =============================================================================

class FileUploadResponse(BaseModel):
    """Schema for file upload response."""
    url: str
    public_id: str
    format: str
    bytes: int


# =============================================================================
# Pagination Schemas
# =============================================================================

class PaginationParams(BaseModel):
    """Pagination parameters."""
    skip: int = Field(0, ge=0)
    limit: int = Field(10, ge=1, le=100)


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List
    total: int
    skip: int
    limit: int
