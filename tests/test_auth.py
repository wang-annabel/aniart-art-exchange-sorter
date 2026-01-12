# tests/test_auth.py

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration"""
    user_data = {
        "email": "newuser@example.com",
        "password": "password123",
        "name": "New User"
    }

    response = await client.post("/auth/register", json = user_data)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == user_data["email"]
    assert "id" in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registering with duplicate email fails"""
    user_data = {
        "email": "duplicate@example.com",
        "password": "password123"
    }

    # First registration should succeed
    response = await client.post("/auth/register", json = user_data)
    assert response.status_code == 201

    # Second registration should fail
    response = await client.post("/auth/register", json = user_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """Test user login"""
    # Register user first
    user_data = {
        "email": "login@example.com",
        "password": "password123"
    }
    await client.post("/auth/register", json = user_data)

    # Login
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }

    response = await client.post("/auth/jwt/login", data = login_data)

    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_get_current_user(authenticated_client: AsyncClient):
    """Test getting current user info"""
    response = await authenticated_client.get("/me")

    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["name"] == "Test User"