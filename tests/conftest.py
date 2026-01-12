# tests/conftest.py

import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
import os

from app.app import app, uploaded_files_cache, matching_cache
from app.db import Base, get_async_session


# Test database URL - use a separate test database
TEST_DATABASE_URL = 'sqlite+aiosqlite:///./test.db'
# Create test engine
test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass = NullPool,
)
test_async_session_maker = async_sessionmaker(
    test_engine,
    expire_on_commit = False
)


@pytest.fixture(scope = "function")
async def setup_database():
    """Create and drop database tables for each test"""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(setup_database) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for tests"""
    async with test_async_session_maker() as session:
        yield session


@pytest.fixture
def override_get_db(db_session: AsyncSession):
    """Override the get_async_session dependency"""

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_async_session] = _override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client(override_get_db) -> AsyncGenerator[AsyncClient, None]:
    """Provide an async HTTP client for testing"""
    # Clear caches before each test
    uploaded_files_cache.clear()
    matching_cache.clear()

    transport = ASGITransport(app = app)
    async with AsyncClient(transport = transport, base_url = "http://test") as ac:
        yield ac


@pytest.fixture
async def authenticated_client(client: AsyncClient, db_session: AsyncSession) -> AsyncGenerator[
    AsyncClient, None]:
    """Provide an authenticated client with a test user"""
    # Register a test user
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "name": "Test User"
    }

    response = await client.post("/auth/register", json = user_data)
    assert response.status_code == 201

    # Login to get token
    login_data = {
        "username": user_data["email"],
        "password": user_data["password"]
    }

    response = await client.post("/auth/jwt/login", data = login_data)
    assert response.status_code == 200

    token = response.json()["access_token"]

    # Add token to client headers
    client.headers["Authorization"] = f"Bearer {token}"

    yield client


# Test data fixtures
@pytest.fixture
def test_data_dir():
    """Get the test_input directory path"""
    return os.path.join(os.path.dirname(__file__), "test_input")


@pytest.fixture
def input_short_csv(test_data_dir):
    """Path to input_short.csv"""
    return os.path.join(test_data_dir, "input_short.csv")


@pytest.fixture
def raw_form_data_csv(test_data_dir):
    """Path to raw_form_data.csv"""
    return os.path.join(test_data_dir, "raw_form_data.csv")


@pytest.fixture
def raw_form_data_1participant_csv(test_data_dir):
    """Path to raw_form_data_1participant.csv"""
    return os.path.join(test_data_dir, "raw_form_data_1participant.csv")


@pytest.fixture
def raw_form_data_3participants_csv(test_data_dir):
    """Path to raw_form_data_3participants.csv"""
    return os.path.join(test_data_dir, "raw_form_data_3participants.csv")


@pytest.fixture
def raw_form_data_30participants_csv(test_data_dir):
    """Path to raw_form_data_30participants.csv"""
    return os.path.join(test_data_dir, "raw_form_data_30participants.csv")