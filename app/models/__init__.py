"""
SQLAlchemy models for P2P Palestine.
"""
import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    Column,
    Integer,
    String,
    Numeric,
    DateTime,
    ForeignKey,
    Enum,
    Boolean,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class UserRole(enum.Enum):
    """User roles in the system."""
    USER = "USER"
    ADMIN = "ADMIN"


class OrderType(enum.Enum):
    """Order types: BUY or SELL."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(enum.Enum):
    """Order status."""
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    REJECTED = "REJECTED"


class TransactionStatus(enum.Enum):
    """Transaction status - Escrow State Machine."""
    MATCHED = "MATCHED"
    ESCROW_LOCKED = "ESCROW_LOCKED"
    COMPLETED = "COMPLETED"
    DISPUTED = "DISPUTED"


class Currency(enum.Enum):
    """Fiat currencies supported."""
    USD = "USD"
    ILS = "ILS"
    JOD = "JOD"


class BlockchainNetwork(enum.Enum):
    """Blockchain networks supported."""
    TRX = "TRX"
    BNB = "BNB"
    SOL = "SOL"
    ETH = "ETH"


class User(Base):
    """User model with encrypted sensitive data."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), default=UserRole.USER, nullable=False)
    
    # Encrypted sensitive data (only visible to admins)
    bank_details_encrypted = Column(Text, nullable=True)  # Bank account info
    wallet_addresses_encrypted = Column(Text, nullable=True)  # Crypto wallet addresses
    
    # Public identity (anonymous to other users)
    public_display_name = Column(String(50), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)  # KYC verified
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    orders = relationship("Order", back_populates="creator", foreign_keys="Order.creator_id")
    transactions_as_initiator = relationship("Transaction", back_populates="initiator", foreign_keys="Transaction.initiator_id")
    transactions_as_counterparty = relationship("Transaction", back_populates="counterparty", foreign_keys="Transaction.counterparty_id")

    def get_masked_identity(self) -> str:
        """Return masked identity for public display."""
        if self.public_display_name:
            return self.public_display_name
        return f"User***{str(self.id)[-4:]}"


class ExchangeRate(Base):
    """Exchange rates managed by admin."""
    __tablename__ = "exchange_rates"

    id = Column(Integer, primary_key=True, index=True)
    base_currency = Column(String(3), default="USD", nullable=False)
    target_currency = Column(Enum(Currency), nullable=False)
    rate = Column(Numeric(10, 6), nullable=False)
    
    # Admin who updated this rate
    updated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    updater = relationship("User", backref="exchange_rates_updated")


class Order(Base):
    """Order model for BUY/SELL listings."""
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    order_type = Column(Enum(OrderType), nullable=False)
    
    # Amount range
    min_amount = Column(Numeric(12, 2), nullable=False)
    max_amount = Column(Numeric(12, 2), nullable=False)
    
    # Commission (0% - 3.5%)
    commission = Column(Numeric(5, 4), nullable=False)  # e.g., 0.0350 for 3.5%
    
    # Currency and network
    currency = Column(Enum(Currency), nullable=False)
    blockchain_network = Column(Enum(BlockchainNetwork), nullable=False)
    
    # Status
    status = Column(Enum(OrderStatus), default=OrderStatus.PENDING, nullable=False)
    
    # Creator
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Rejection reason (if rejected by admin)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    creator = relationship("User", back_populates="orders", foreign_keys=[creator_id])
    transactions = relationship("Transaction", back_populates="order")


class Transaction(Base):
    """Transaction model representing matched order between buyer and seller."""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Linked order
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    
    # Parties involved
    initiator_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # User who accepted the order
    counterparty_id = Column(Integer, ForeignKey("users.id"), nullable=False)  # Order creator
    
    # Transaction amount
    base_amount = Column(Numeric(12, 2), nullable=False)  # The base USDT amount
    
    # Calculated amounts based on commission engine
    buyer_pays = Column(Numeric(12, 2), nullable=False)  # What buyer pays (with fees)
    seller_receives = Column(Numeric(12, 2), nullable=False)  # What seller receives (after fees)
    platform_fee = Column(Numeric(12, 2), nullable=False)  # Platform fee (0.75% per side)
    
    # Escrow state machine
    status = Column(Enum(TransactionStatus), default=TransactionStatus.MATCHED, nullable=False)
    
    # Payment details (encrypted)
    payment_proof_url = Column(String(500), nullable=True)  # Cloudinary URL for proof of funds
    payment_reference = Column(String(100), nullable=True)  # Bank transfer reference
    
    # Dispute information
    dispute_reason = Column(Text, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)  # Admin who resolved
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Relationships
    order = relationship("Order", back_populates="transactions")
    initiator = relationship("User", back_populates="transactions_as_initiator", foreign_keys=[initiator_id])
    counterparty = relationship("User", back_populates="transactions_as_counterparty", foreign_keys=[counterparty_id])
    resolver = relationship("User", foreign_keys=[resolved_by], backref="resolved_transactions")


class AuditLog(Base):
    """Audit log for tracking all financial operations."""
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50), nullable=False)  # e.g., "Order", "Transaction"
    entity_id = Column(Integer, nullable=True)
    old_values = Column(Text, nullable=True)  # JSON string of old values
    new_values = Column(Text, nullable=True)  # JSON string of new values
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", backref="audit_logs")
