"""Tests for the properties API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from tests.conftest import PROPERTY_ID, PROPERTY_ID_2, TENANT_ID


def _make_property(pid, name="Test Hotel", code="PROP1"):
    prop = MagicMock()
    prop.id = pid
    prop.name = name
    prop.code = code
    prop.timezone = "America/New_York"
    prop.is_active = True
    prop.departments = []
    return prop


def _mock_db_result(items):
    """Create a mock db result that works with result.scalars().all()."""
    result = MagicMock()
    scalars_mock = MagicMock()
    scalars_mock.all.return_value = items
    result.scalars.return_value = scalars_mock
    result.scalar_one_or_none.return_value = items[0] if items else None
    return result


class TestListProperties:
    async def test_admin_sees_all_properties(self, admin_client, mock_db):
        props = [_make_property(PROPERTY_ID, "Hotel A"), _make_property(PROPERTY_ID_2, "Hotel B")]
        mock_db.execute.return_value = _mock_db_result(props)

        resp = await admin_client.get("/api/v1/properties")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2

    async def test_manager_sees_assigned_only(self, manager_client, mock_db):
        props = [_make_property(PROPERTY_ID, "Assigned Hotel")]
        mock_db.execute.return_value = _mock_db_result(props)

        resp = await manager_client.get("/api/v1/properties")
        assert resp.status_code == 200

    async def test_unauthenticated_returns_401(self, unauth_client):
        resp = await unauth_client.get("/api/v1/properties")
        assert resp.status_code == 401


class TestGetProperty:
    async def test_get_property_by_id(self, admin_client, mock_db):
        prop = _make_property(PROPERTY_ID)
        mock_db.execute.return_value = _mock_db_result([prop])

        resp = await admin_client.get(f"/api/v1/properties/{PROPERTY_ID}")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Test Hotel"

    async def test_get_property_not_found(self, admin_client, mock_db):
        mock_db.execute.return_value = _mock_db_result([])

        resp = await admin_client.get(f"/api/v1/properties/{PROPERTY_ID}")
        assert resp.status_code == 404

    async def test_manager_cannot_access_unassigned_property(self, manager_client):
        unassigned_id = uuid.UUID("00000000-0000-0000-0000-000000000099")
        resp = await manager_client.get(f"/api/v1/properties/{unassigned_id}")
        assert resp.status_code == 403
