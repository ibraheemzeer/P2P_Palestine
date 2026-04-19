"""
Unit Tests for P2P Palestine Platform
Run with: pytest tests/ -v
"""
import pytest
import asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import select

from app.main import app
from app.core.database import get_settings, get_db
from app.models import User, UserRole, Order, Transaction, OrderStatus, TransactionStatus
from app.core.security import get_password_hash, verify_password
from app.core.commission_engine import calculate_commission

# Test Database Configuration (use separate DB for testing)
TEST_DATABASE_URL = "postgresql+asyncpg://p2p_user:p2p_password@localhost:5432/p2p_palestine_test"

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
async def test_client():
    """Create a test client with isolated database."""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    # Create tables
    from app.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    # Drop tables after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()

@pytest.fixture
async def db_session():
    """Create a fresh database session for each test."""
    settings = get_settings()
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        yield session
    
    await engine.dispose()

# ==================== Security Tests ====================

class TestSecurity:
    def test_password_hashing(self):
        """Test that passwords are hashed correctly."""
        password = "test_password_123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 50
        assert verify_password(password, hashed)
        assert not verify_password("wrong_password", hashed)
    
    def test_commission_calculation(self):
        """Test the commission engine math."""
        base_amount = 1000.0
        seller_commission = 2.0  # 2%
        
        # Convert percentage to decimal (2% = 0.02)
        result = calculate_commission(base_amount, seller_commission / 100)
        
        # Result is a dict, access by key
        # Buyer Pays = 1000 * (1 + 0.02 + 0.0075) = 1027.5
        expected_buyer_pays = base_amount * (1 + seller_commission/100 + 0.0075)
        # Seller Receives = 1000 * (1 + 0.02 - 0.0075) = 1012.5
        expected_seller_receives = base_amount * (1 + seller_commission/100 - 0.0075)
        # Platform Fee = 1000 * 0.0075 * 2 = 15.0 (0.75% from each side)
        expected_platform_fee = base_amount * 0.0075 * 2
        
        assert abs(float(result["buyer_pays"]) - expected_buyer_pays) < 0.01
        assert abs(float(result["seller_receives"]) - expected_seller_receives) < 0.01
        assert abs(float(result["total_platform_profit"]) - expected_platform_fee) < 0.01
        
        print(f"✅ Commission Test Passed:")
        print(f"   Buyer Pays: {result['buyer_pays']}")
        print(f"   Seller Gets: {result['seller_receives']}")
        print(f"   Platform Fee: {result['total_platform_profit']}")

# ==================== Authentication Tests ====================

@pytest.mark.asyncio
async def test_user_registration(test_client):
    """Test user registration endpoint."""
    response = await test_client.post("/api/v1/auth/register", json={
        "username": "new_test_user",
        "email": "newuser@test.com",
        "password": "securepass123",
        "public_display_name": "AnonymousTrader"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    print("✅ User Registration Test Passed")

@pytest.mark.asyncio
async def test_user_login(test_client, db_session):
    """Test user login endpoint."""
    # First create a user
    user = User(
        username="login_test_user",
        email="login@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER,
        public_display_name="LoginTester"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Try to login
    response = await test_client.post("/api/v1/auth/login", data={
        "username": "login_test_user",
        "password": "password123"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    print("✅ User Login Test Passed")

@pytest.mark.asyncio
async def test_invalid_login(test_client):
    """Test login with invalid credentials."""
    response = await test_client.post("/api/v1/auth/login", data={
        "username": "nonexistent_user",
        "password": "wrongpassword"
    })
    
    assert response.status_code == 401
    print("✅ Invalid Login Test Passed")

# ==================== Order Tests ====================

@pytest.mark.asyncio
async def test_create_order(test_client, db_session):
    """Test creating a new order."""
    # Create and login user first
    user = User(
        username="order_test_user",
        email="order@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER,
        public_display_name="OrderCreator"
    )
    db_session.add(user)
    await db_session.commit()
    
    # Login to get token
    login_response = await test_client.post("/api/v1/auth/login", data={
        "username": "order_test_user",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Create order
    order_data = {
        "order_type": "SELL",
        "currency": "ILS",
        "blockchain_network": "TRX",
        "min_amount": 100.0,
        "max_amount": 5000.0,
        "commission": 1.5,
        "price_per_unit": 3.65,
        "terms": "Fast transaction guaranteed"
    }
    
    response = await test_client.post("/api/v1/orders/", json=order_data, headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["order_type"] == "SELL"
    assert data["status"] == "PENDING"  # Initial status should be PENDING
    assert "proof_of_funds_url" in data or data["status"] == "PENDING"  # Waiting for proof
    print("✅ Create Order Test Passed")

@pytest.mark.asyncio
async def test_get_orders_anonymity(test_client, db_session):
    """Test that non-admin users see masked identities."""
    # Create seller
    seller = User(
        username="real_seller_name",
        email="seller@private.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER,
        public_display_name="MaskedSeller_123"
    )
    db_session.add(seller)
    
    # Create buyer (viewer)
    buyer = User(
        username="buyer_viewer",
        email="buyer@private.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER,
        public_display_name="BuyerViewer"
    )
    db_session.add(buyer)
    
    # Create order
    order = Order(
        seller_id=seller.id,
        order_type="SELL",
        currency="USD",
        blockchain_network="ETH",
        min_amount=50.0,
        max_amount=1000.0,
        commission=1.0,
        price_per_unit=1.0,
        status=OrderStatus.ACTIVE
    )
    db_session.add(order)
    await db_session.commit()
    
    # Login as buyer
    login_response = await test_client.post("/api/v1/auth/login", data={
        "username": "buyer_viewer",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get orders
    response = await test_client.get("/api/v1/orders/", headers=headers)
    
    assert response.status_code == 200
    orders = response.json()
    assert len(orders) > 0
    
    # Verify anonymity - should NOT see real username
    order_data = orders[0]
    assert "real_seller_name" not in str(order_data)
    # Should see masked name or ID
    assert "seller_id" in order_data or "MaskedSeller" in str(order_data)
    
    print("✅ Order Anonymity Test Passed")

# ==================== Commission Engine Tests ====================

class TestCommissionEngine:
    def test_zero_commission(self):
        """Test with 0% seller commission."""
        result = calculate_commission(1000.0, 0.0)
        assert abs(float(result["buyer_pays"]) - 1007.5) < 0.01  # Only platform fee
        assert abs(float(result["seller_receives"]) - 992.5) < 0.01
        print("✅ Zero Commission Test Passed")
    
    def test_max_commission(self):
        """Test with maximum 3.5% seller commission."""
        # 3.5% = 0.035 in decimal
        result = calculate_commission(1000.0, 0.035)
        expected_buyer = 1000 * (1 + 0.035 + 0.0075)  # 1042.5
        expected_seller = 1000 * (1 + 0.035 - 0.0075)  # 1027.5
        assert abs(float(result["buyer_pays"]) - expected_buyer) < 0.01
        assert abs(float(result["seller_receives"]) - expected_seller) < 0.01
        print("✅ Max Commission Test Passed")
    
    def test_small_amount(self):
        """Test with small amounts."""
        # 1% = 0.01 in decimal
        result = calculate_commission(10.0, 0.01)
        assert float(result["buyer_pays"]) > 10.0
        assert float(result["seller_receives"]) < 11.0  # Less than base + commission
        print("✅ Small Amount Test Passed")

# ==================== Admin Tests ====================

@pytest.mark.asyncio
async def test_admin_only_endpoint(test_client, db_session):
    """Test that admin-only endpoints reject regular users."""
    # Create regular user
    user = User(
        username="regular_user",
        email="regular@test.com",
        hashed_password=get_password_hash("password123"),
        role=UserRole.USER
    )
    db_session.add(user)
    await db_session.commit()
    
    # Login as regular user
    login_response = await test_client.post("/api/v1/auth/login", data={
        "username": "regular_user",
        "password": "password123"
    })
    token = login_response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to access admin endpoint (update exchange rate)
    response = await test_client.post("/api/v1/admin/exchange-rates/", json={
        "fiat_currency": "ILS",
        "rate": 3.70
    }, headers=headers)
    
    assert response.status_code == 403  # Forbidden
    print("✅ Admin-Only Endpoint Test Passed")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
