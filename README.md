# P2P Palestine - Project Documentation

## 📋 Project Overview
**P2P Palestine** is a secure Peer-to-Peer exchange platform for trading USDT against local fiat currencies (USD, ILS, JOD). The system acts as a "Trusted Third Party" (Manual Escrow) where the Admin holds both Crypto and Fiat assets during transactions to ensure zero-risk for all parties.

### Core Features
- **Escrow-Based Trading**: Secure manual escrow system with state machine management
- **Multi-Currency Support**: USD, ILS, JOD fiat currencies
- **Multi-Blockchain Support**: TRX, BNB, SOL, ETH networks
- **Privacy-First**: Anonymous user identities for regular users, full visibility for admins only
- **Dynamic Commission Engine**: Configurable fees (0% - 3.5%) + fixed platform fee (0.75% per side)
- **KYC Verification**: Cloudinary integration for Proof of Funds image uploads

---

## 🏗️ System Architecture

### Tech Stack
- **Backend**: Python FastAPI
- **Database**: PostgreSQL 15 (Async via `asyncpg`)
- **ORM**: SQLAlchemy 2.0 (Async)
- **Validation**: Pydantic v2
- **Authentication**: JWT (python-jose) + Passlib (bcrypt)
- **Image Storage**: Cloudinary API
- **Containerization**: Docker & Docker Compose
- **Migrations**: Alembic

### Project Structure
```
app/
├── __init__.py
├── main.py                 # FastAPI application entry point
├── core/
│   ├── __init__.py
│   ├── config.py           # Pydantic Settings & environment management
│   ├── database.py         # Async SQLAlchemy engine & session management
│   ├── security.py         # JWT auth, password hashing, encryption utilities
│   └── commission_engine.py # Business logic for fee calculations
├── models/
│   └── __init__.py         # SQLAlchemy models (User, Order, Transaction, etc.)
├── schemas/
│   └── __init__.py         # Pydantic v2 schemas for validation
├── services/
│   ├── cloudinary_service.py # Image upload service
│   └── auth.py             # Authentication dependencies & logic
├── routes/
│   ├── users.py            # User registration & login endpoints
│   └── orders.py           # Order management endpoints
└── utils/
    └── helpers.py          # Utility functions

alembic/                    # Database migrations
├── versions/               # Migration scripts
├── env.py                  # Alembic environment configuration
└── alembic.ini             # Alembic configuration

docker-compose.yml          # Docker services orchestration
Dockerfile                  # Application container definition
.env                        # Environment variables
requirements.txt            # Python dependencies
```

---

## 🗄️ Database Models

### User Model
- **Fields**: 
  - `id`, `email`, `hashed_password`, `role` (USER/ADMIN)
  - `public_display_name` (anonymous identity)
  - `bank_details` (JSONB, encrypted)
  - `crypto_addresses` (JSONB, encrypted)
  - `is_active`, `created_at`, `updated_at`
- **Privacy**: Real identities visible only to ADMIN role

### Order Model
- **Fields**:
  - `id`, `user_id` (creator), `type` (BUY/SELL)
  - `currency` (USD/ILS/JOD), `blockchain_network` (TRX/BNB/SOL/ETH)
  - `min_amount`, `max_amount`, `commission` (0-3.5%)
  - `status` (PENDING/ACTIVE/REJECTED)
  - `proof_of_funds_url` (Cloudinary URL)
  - `created_at`, `updated_at`

### Transaction Model
- **Fields**:
  - `id`, `order_id`, `buyer_id`, `seller_id`
  - `base_amount`, `exchange_rate`, `currency`
  - `buyer_pays`, `seller_receives`, `platform_fee`
  - `status` (MATCHED/ESCROW_LOCKED/COMPLETED/DISPUTED)
  - `escrow_locked_at`, `completed_at`, `disputed_at`

### ExchangeRate Model
- **Fields**: `id`, `currency_pair`, `rate`, `updated_by` (admin), `created_at`

### AuditLog Model
- **Fields**: `id`, `user_id`, `action`, `entity_type`, `entity_id`, `details` (JSONB), `timestamp`

---

## 🔐 Authentication & Security

### JWT Authentication
- **Algorithm**: HS256
- **Token Expiry**: 30 minutes (access token)
- **Password Hashing**: bcrypt via passlib
- **Dependencies**:
  - `get_current_user()`: Validates JWT and returns current user
  - `get_current_admin()`: Restricts access to ADMIN role only

### Endpoints
| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | User registration | No |
| POST | `/auth/login` | Login & get JWT token | No |
| GET | `/users/me` | Get current user profile | Yes |
| GET | `/users/me/admin` | Get current admin profile | Admin Only |

---

## 💰 Commission Engine

### Fee Structure
- **Platform Fee**: Fixed 0.75% per side (Total 1.5%)
- **Seller Commission**: Dynamic 0% - 3.5% (set by seller)

### Calculation Logic
```python
# Buyer pays base amount + seller commission + platform fee
buyer_pays = base_amount * (1 + seller_commission + 0.0075)

# Seller receives base amount + seller commission - platform fee
seller_receives = base_amount * (1 + seller_commission - 0.0075)

# Platform profit
platform_fee_per_side = base_amount * 0.0075
total_platform_fee = platform_fee_per_side * 2
```

### Example Calculation
For a trade of **1000 USDT** with **2% seller commission**:
- **Buyer Pays**: 1000 × (1 + 0.02 + 0.0075) = **1027.50 USDT**
- **Seller Receives**: 1000 × (1 + 0.02 - 0.0075) = **1012.50 USDT**
- **Platform Fee**: 7.50 USDT per side = **15.00 USDT total**

---

## ☁️ Cloudinary Integration

### Configuration
Environment variables required in `.env`:
```bash
CLOUDINARY_CLOUD_NAME=your_cloud_name_here
CLOUDINARY_API_KEY=your_api_key_here
CLOUDINARY_API_SECRET=your_api_secret_here
```

### Features
- **Upload Folder**: All proof of funds images stored in `p2p_proofs` folder
- **Endpoint**: `POST /orders/` accepts `UploadFile` for proof of funds
- **Security**: Files uploaded server-side, URLs stored in database
- **Organization**: Structured folder hierarchy for easy management

### Usage
```python
from app.services.cloudinary_service import upload_proof_of_funds

# Upload image file
result = await upload_proof_of_funds(file=upload_file, user_id=user_id)
# Returns: {"url": "https://res.cloudinary.com/...", "public_id": "..."}
```

---

## 🚀 Order Management

### Order Lifecycle
1. **Creation**: User creates order with Proof of Funds → Status: `PENDING`
2. **Admin Review**: Admin verifies proof → Status: `ACTIVE` or `REJECTED`
3. **Matching**: Buyer/Seller matched → Transaction created → Status: `MATCHED`
4. **Escrow**: Assets locked by admin → Status: `ESCROW_LOCKED`
5. **Completion**: Trade completed → Status: `COMPLETED`
6. **Dispute** (Optional): Dispute raised → Status: `DISPUTED`

### Privacy Mode (Anonymous Identity)
- **Regular Users**: See masked creator names (e.g., `User_123`)
- **Admins**: See full user details including real identity
- **Implementation**: Automatic masking in `GET /orders/` response based on requester role

### Endpoints
| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/orders/` | Create new order (with proof upload) | User |
| GET | `/orders/` | List all orders (anonymous mode for non-admins) | User |
| GET | `/orders/{order_id}` | Get single order details | User |
| PUT | `/orders/{order_id}` | Update order (Admin only) | Admin |
| DELETE | `/orders/{order_id}` | Cancel order | User/Admin |

---

## 🐳 Docker Setup

### Services
1. **PostgreSQL 15** (`db`)
   - Port: 5432
   - Database: `p2p_palestine_db`
   - User: `p2p_user`
   - Password: `p2p_password`
   - Volume: `postgres_data` (persistent storage)
   - Health check enabled

2. **pgAdmin 4** (`pgadmin`)
   - Port: 5050
   - Email: `admin@p2p.com`
   - Password: `admin123`

3. **FastAPI App** (`api`)
   - Port: 8000
   - Auto-reload enabled for development
   - Depends on `db` service

### Network
- Custom bridge network: `p2p_network`
- Secure inter-service communication

### Quick Start
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your credentials (especially Cloudinary)

# Start all services
docker compose up -d --build

# View logs
docker compose logs -f api

# Stop services
docker compose down
```

### Access Points
- **API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **pgAdmin**: http://localhost:5050

---

## 🔄 Database Migrations (Alembic)

### Setup
```bash
# Initialize Alembic (already done)
alembic init alembic

# Generate new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1
```

### Configuration
- **Target Metadata**: Automatically detected from `app.models`
- **Async Support**: Configured for `asyncpg` engine
- **Environment**: Reads `DATABASE_URL` from `.env`

---

## 📝 Environment Variables

### Required Variables (.env)
```bash
# Database
DATABASE_URL=postgresql+asyncpg://p2p_user:p2p_password@db:5432/p2p_palestine_db

# JWT Security
SECRET_KEY=your-super-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Cloudinary
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Application
ENVIRONMENT=development  # or production
DEBUG=True
```

---

## ✅ Current Implementation Status

| Component | Status | Details |
|-----------|--------|---------|
| Database Setup | ✅ Complete | Async SQLAlchemy + PostgreSQL + Alembic |
| Data Models | ✅ Complete | User, Order, Transaction, ExchangeRate, AuditLog |
| Authentication | ✅ Complete | JWT, Password Hashing, Role-based Access |
| Commission Engine | ✅ Complete | Dynamic pricing with 0.75% platform fee |
| Cloudinary Integration | ✅ Complete | Proof of Funds upload with organized folders |
| Order Management | ✅ Complete | CRUD with anonymous mode & status workflow |
| Docker Setup | ✅ Complete | Multi-service with health checks & persistence |
| API Documentation | ✅ Complete | Swagger UI & ReDoc auto-generated |

---

## 🎯 Next Steps (Roadmap)

1. **Transaction Workflow**: Implement full escrow state machine
2. **Admin Dashboard**: Endpoints for order approval, rate management, dispute resolution
3. **Real-time Notifications**: WebSocket integration for order status updates
4. **Enhanced KYC**: Multi-document verification workflow
5. **Rate Limiting**: Protect APIs from abuse
6. **Testing Suite**: Unit tests (pytest) + Integration tests
7. **CI/CD Pipeline**: GitHub Actions for automated testing & deployment
8. **Monitoring**: Logging, metrics, and alerting setup

---

## 📚 API Reference

Full interactive documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key endpoint categories:
- `/auth/*` - Authentication & Registration
- `/users/*` - User Profile Management
- `/orders/*` - Order Creation & Management
- `/transactions/*` - Transaction & Escrow Management (Coming Soon)
- `/admin/*` - Admin-only Operations (Coming Soon)

---

## 🛡️ Security Considerations

- **Data Encryption**: Sensitive fields (bank details, crypto addresses) encrypted at rest
- **Password Security**: bcrypt hashing with salt
- **JWT Best Practices**: Short-lived tokens, secure cookie storage recommended
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Pydantic validation & sanitization
- **Rate Limiting**: To be implemented
- **Audit Logging**: All financial operations tracked in AuditLog

---

## 🤝 Contributing

This project follows a modular architecture. When adding new features:
1. Create models in `app/models/`
2. Define schemas in `app/schemas/`
3. Implement business logic in `app/services/`
4. Add routes in `app/routes/`
5. Create Alembic migration for schema changes
6. Update this documentation

---

**Last Updated**: December 2024  
**Version**: 1.0.0 (MVP Foundation Complete)
