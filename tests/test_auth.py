"""
Tests for Authentication endpoints.
Covers registration, login, and rate limiting.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient, sample_user_data: dict):
    """Test successful user registration."""
    response = await client.post("/api/v1/auth/register", json=sample_user_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient, sample_user_data: dict, test_user):
    """Test registration with duplicate username fails."""
    # Change email to avoid email conflict
    sample_user_data["email"] = "different@example.com"
    
    response = await client.post("/api/v1/auth/register", json=sample_user_data)
    
    assert response.status_code == 400
    assert "Username already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient, sample_user_data: dict, test_user):
    """Test registration with duplicate email fails."""
    # Change username to avoid username conflict
    sample_user_data["username"] = "differentuser"
    
    response = await client.post("/api/v1/auth/register", json=sample_user_data)
    
    assert response.status_code == 400
    assert "Email already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, test_user: dict):
    """Test successful login."""
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient, test_user: dict):
    """Test login with wrong password fails."""
    login_data = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 401
    assert "Incorrect username or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with non-existent user fails."""
    login_data = {
        "username": "nonexistent",
        "password": "anypassword"
    }
    
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, test_user: dict):
    """Test getting current user info."""
    # First login to get token
    login_data = {
        "username": "testuser",
        "password": "testpassword123"
    }
    login_response = await client.post("/api/v1/auth/login", data=login_data)
    token = login_response.json()["access_token"]
    
    # Get current user
    headers = {"Authorization": f"Bearer {token}"}
    response = await client.get("/api/v1/auth/me", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_rate_limiting_login(client: AsyncClient):
    """Test rate limiting on login endpoint."""
    login_data = {
        "username": "testuser",
        "password": "wrongpassword"
    }
    
    # Make multiple requests to trigger rate limit
    for _ in range(15):
        await client.post("/api/v1/auth/login", data=login_data)
    
    # Next request should be rate limited
    response = await client.post("/api/v1/auth/login", data=login_data)
    
    # Should return 429 Too Many Requests
    assert response.status_code == 429
    assert "Too many requests" in response.json()["detail"]
