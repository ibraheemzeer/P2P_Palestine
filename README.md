# P2P_Palestine

## Project Overview
Secure P2P platform for trading USDT against local fiat (USD, ILS, JOD) with manual escrow.

## Tech Stack
- **Backend**: Python FastAPI
- **Database**: PostgreSQL (SQLAlchemy)
- **Validation**: Pydantic v2
- **Storage**: Cloudinary API
- **Auth**: JWT

## Project Structure
```
app/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── config.py          # Pydantic configuration
│   ├── database.py        # SQLAlchemy session management
│   ├── security.py        # Encryption, JWT utilities
│   └── commission_engine.py  # Business logic for fees
├── models/
│   └── __init__.py        # SQLAlchemy models (User, Order, Transaction, etc.)
└── schemas/
    └── __init__.py        # Pydantic schemas for API validation
```

## Core Entities
- **Users**: USER and ADMIN roles with encrypted sensitive data
- **Orders**: BUY/SELL listings with commission (0%-3.5%)
- **Transactions**: Escrow state machine (MATCHED → ESCROW_LOCKED → COMPLETED/DISPUTED)
- **ExchangeRates**: Admin-managed fiat rates
- **AuditLog**: Financial operation tracking

## Commission Engine
- Platform Fee: 0.75% per side (1.5% total)
- Formula:
  - Buyer_Pays = Base_Amount × (1 + Seller_Commission + 0.0075)
  - Seller_Receives = Base_Amount × (1 + Seller_Commission - 0.0075)

## Setup
```bash
pip install fastapi sqlalchemy pydantic python-jose cryptography psycopg2-binary
```

## Next Steps
1. Create FastAPI application and routers
2. Implement authentication endpoints
3. Build order management APIs
4. Implement transaction/escrow flow
5. Add Cloudinary integration for proof uploads