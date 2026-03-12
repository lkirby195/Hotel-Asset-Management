"""Shared test fixtures for the hotel asset management backend."""

import uuid
from datetime import date, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies import get_current_user, get_db_session, require_property_access, require_role
from app.main import app
from app.models.user import User


# ── Shared IDs ────────────────────────────────────────────────────

TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
PROPERTY_ID = uuid.UUID("00000000-0000-0000-0000-000000000010")
PROPERTY_ID_2 = uuid.UUID("00000000-0000-0000-0000-000000000020")
USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000100")
LINE_ITEM_ID = uuid.UUID("00000000-0000-0000-0000-000000001000")
LINE_ITEM_ID_2 = uuid.UUID("00000000-0000-0000-0000-000000002000")
PARENT_LINE_ITEM_ID = uuid.UUID("00000000-0000-0000-0000-000000003000")


# ── Mock User factory ────────────────────────────────────────────

def make_user(
    role: str = "admin",
    user_id: uuid.UUID = USER_ID,
    tenant_id: uuid.UUID = TENANT_ID,
    property_ids: list[uuid.UUID] | None = None,
) -> User:
    """Create a mock User object for testing."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.tenant_id = tenant_id
    user.clerk_id = "clerk_test_123"
    user.email = "test@example.com"
    user.name = "Test User"
    user.role = role
    user.is_active = True
    user.created_at = datetime(2026, 1, 1)
    user.updated_at = datetime(2026, 1, 1)

    # Mock properties (for property access checks)
    mock_props = []
    for pid in (property_ids or [PROPERTY_ID]):
        prop = MagicMock()
        prop.id = pid
        mock_props.append(prop)
    user.properties = mock_props

    # Real has_role implementation
    role_hierarchy = {"admin": 4, "executive": 3, "operator": 2, "manager": 1}
    user.has_role = lambda min_role: role_hierarchy.get(role, 0) >= role_hierarchy.get(min_role, 0)

    return user


# ── Mock DB session ──────────────────────────────────────────────

@pytest.fixture
def mock_db():
    """Create a mock async DB session."""
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.execute = AsyncMock()
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.delete = AsyncMock()
    return session


# ── Mock Redis ───────────────────────────────────────────────────

@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock()
    redis.scan_iter = MagicMock(return_value=AsyncMock())
    redis.delete = AsyncMock()
    return redis


# ── FastAPI test client with dependency overrides ────────────────

@pytest.fixture
def admin_user():
    return make_user(role="admin")


@pytest.fixture
def exec_user():
    return make_user(role="executive")


@pytest.fixture
def manager_user():
    return make_user(role="manager", property_ids=[PROPERTY_ID])


@pytest.fixture
def operator_user():
    return make_user(role="operator", property_ids=[PROPERTY_ID])


def override_deps(user, db_session=None, redis_client=None):
    """Apply FastAPI dependency overrides for testing."""
    overrides = {}

    # Override auth
    async def _get_user():
        return user

    overrides[get_current_user] = _get_user

    # Override require_role for all role levels
    for role in ("admin", "executive", "operator", "manager"):
        _role = role

        async def _check_role(r=_role):
            if not user.has_role(r):
                from fastapi import HTTPException
                raise HTTPException(status_code=403, detail=f"Requires {r} role or higher")
            return user

        overrides[require_role(role)] = _check_role

    # Override property access
    async def _property_access(property_id: uuid.UUID):
        if user.role in ("executive", "admin"):
            return property_id
        user_pids = {p.id for p in user.properties}
        if property_id not in user_pids:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="You do not have access to this property")
        return property_id

    overrides[require_property_access] = _property_access

    # Override DB session
    if db_session is not None:
        async def _get_db():
            yield db_session

        overrides[get_db_session] = _get_db

    # Override Redis
    if redis_client is not None:
        from app.cache.redis_client import get_redis

        async def _get_redis():
            return redis_client

        overrides[get_redis] = _get_redis

    return overrides


@pytest.fixture
async def admin_client(admin_user, mock_db, mock_redis):
    """AsyncClient authenticated as admin with mocked DB and Redis."""
    app.dependency_overrides = override_deps(admin_user, mock_db, mock_redis)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides = {}


@pytest.fixture
async def exec_client(exec_user, mock_db, mock_redis):
    """AsyncClient authenticated as executive."""
    app.dependency_overrides = override_deps(exec_user, mock_db, mock_redis)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides = {}


@pytest.fixture
async def manager_client(manager_user, mock_db, mock_redis):
    """AsyncClient authenticated as manager."""
    app.dependency_overrides = override_deps(manager_user, mock_db, mock_redis)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides = {}


@pytest.fixture
async def operator_client(operator_user, mock_db, mock_redis):
    """AsyncClient authenticated as operator."""
    app.dependency_overrides = override_deps(operator_user, mock_db, mock_redis)
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides = {}


@pytest.fixture
async def unauth_client():
    """AsyncClient with no auth overrides (tests 401)."""
    app.dependency_overrides = {}
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client
    app.dependency_overrides = {}
