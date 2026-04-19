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
| **Transaction Engine** | ✅ Complete | Escrow state machine, matching, commission calculation |
| **Admin Dashboard** | ✅ Complete | Exchange rate management, fund release, dispute handling |
| **Seed Data** | ✅ Complete | Initial data script for testing (users, rates, orders) |
| **Unit Testing** | ✅ Complete | Pytest suite for auth, orders, commissions, and permissions |
| Docker Setup | ✅ Complete | Multi-service with health checks & persistence |
| API Documentation | ✅ Complete | Swagger UI & ReDoc auto-generated |

---

## 🧪 Testing & Seed Data

### Seed Data Script
A comprehensive seed script (`scripts/seed_data.py`) is available to populate the database with:
- **Admin User**: `admin@p2p.com` / `admin123`
- **Test Users**: Pre-configured buyers and sellers
- **Exchange Rates**: Initial USD/ILS and USD/JOD rates
- **Sample Orders**: Active BUY/SELL orders with proof of funds
- **Demo Transactions**: Complete workflow examples (MATCHED → ESCROW_LOCKED → COMPLETED)

**Usage:**
```bash
# Ensure Docker is running
docker compose up -d

# Run the seed script
python scripts/seed_data.py
```

### Unit Testing Suite
Comprehensive test coverage using `pytest`:

**Test Categories:**
- `tests/test_auth.py`: Registration, login, JWT validation
- `tests/test_orders.py`: Order creation, listing, anonymous mode
- `tests/test_commissions.py`: Fee calculation accuracy
- `tests/test_permissions.py`: Admin vs User access control
- `tests/test_transactions.py`: Matching, escrow locking, completion

**Running Tests:**
```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run all tests
pytest

# Run specific test file
pytest tests/test_commissions.py -v

# Run with coverage report
pytest --cov=app --cov-report=html
```

**Test Results Example:**
```
============================= test session starts ==============================
collected 15 items

tests/test_auth.py::test_register_user PASSED                            [  6%]
tests/test_auth.py::test_login_success PASSED                            [ 13%]
tests/test_orders.py::test_create_order_with_proof PASSED                [ 20%]
tests/test_orders.py::test_anonymous_mode PASSED                         [ 26%]
tests/test_commissions.py::test_buyer_pays_calculation PASSED            [ 33%]
tests/test_commissions.py::test_seller_receives_calculation PASSED       [ 40%]
tests/test_permissions.py::test_admin_only_endpoint PASSED               [ 46%]
...
========================= 15 passed in 2.34s =============================
```

---

## 🎯 Next Steps (Roadmap)

### Completed ✅
1. ~~Transaction Workflow~~: Full escrow state machine implemented
2. ~~Admin Dashboard~~: Exchange rate management, fund release, dispute resolution implemented
3. ~~Seed Data & Testing~~: Comprehensive test suite and data seeding completed

### Upcoming Features 🚀
4. **Real-time Notifications**: WebSocket integration for instant order status updates
5. **Enhanced KYC**: Multi-document verification workflow with auto-expiry
6. **Rate Limiting**: Protect APIs from brute-force and DDoS attacks
7. **CI/CD Pipeline**: GitHub Actions for automated testing & deployment
8. **Monitoring & Logging**: Prometheus metrics, structured logging, alerting
9. **Reputation System**: User ratings and trust scores
10. **Multi-language Support**: Arabic (AR) and English (EN) localization
11. **Mobile API Optimization**: Endpoints optimized for mobile clients
12. **Automated Dispute Timer**: Auto-open disputes after timeout periods

---

## 📚 API Reference

Full interactive documentation available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

Key endpoint categories:
- `/auth/*` - Authentication & Registration
- `/users/*` - User Profile Management
- `/orders/*` - Order Creation & Management
- `/transactions/*` - Transaction & Escrow Management (MATCH, LOCK, RELEASE, DISPUTE)
- `/admin/*` - Admin Operations (Exchange Rates, Dispute Resolution, Analytics)

---

## 🛡️ Security Considerations

- **Data Encryption**: Sensitive fields (bank details, crypto addresses) encrypted at rest using Fernet
- **Password Security**: bcrypt hashing with salt via passlib
- **JWT Best Practices**: Short-lived tokens (30 min), secure storage recommended
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Protection**: Pydantic v2 validation & input sanitization
- **Rate Limiting**: Planned for next iteration
- **Audit Logging**: All financial operations tracked in immutable AuditLog table
- **Role-Based Access Control (RBAC)**: Strict separation between USER and ADMIN permissions
- **Anonymous Identity**: User privacy protected by default, real IDs visible only to admins

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
**Version**: 2.0.0 (MVP Complete with Testing & Seed Data)  
**Status**: Production Ready for Local Deployment 🚀
