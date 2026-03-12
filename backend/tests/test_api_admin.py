"""Tests for the admin API endpoints."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.conftest import PROPERTY_ID, TENANT_ID, USER_ID, make_user


class TestAdminRoleGating:
    """Verify that non-admin users get 403 on admin endpoints."""

    async def test_manager_cannot_list_users(self, manager_client):
        resp = await manager_client.get("/api/v1/admin/users")
        assert resp.status_code == 403

    async def test_operator_cannot_list_users(self, operator_client):
        resp = await operator_client.get("/api/v1/admin/users")
        assert resp.status_code == 403

    async def test_executive_cannot_list_users(self, exec_client):
        resp = await exec_client.get("/api/v1/admin/users")
        assert resp.status_code == 403

    async def test_manager_cannot_trigger_sync(self, manager_client):
        resp = await manager_client.post("/api/v1/admin/sync")
        assert resp.status_code == 403

    async def test_manager_cannot_create_user(self, manager_client):
        resp = await manager_client.post("/api/v1/admin/users", json={
            "clerk_id": "new_clerk", "email": "new@test.com", "name": "New User",
        })
        assert resp.status_code == 403


class TestAdminUserCRUD:
    """Test user management endpoints as admin."""

    def _make_mock_user(self, user_id=None, name="Test User", role="manager"):
        user = MagicMock()
        user.id = user_id or uuid.uuid4()
        user.tenant_id = TENANT_ID
        user.clerk_id = f"clerk_{user.id}"
        user.email = f"{name.lower().replace(' ', '.')}@test.com"
        user.name = name
        user.role = role
        user.is_active = True
        user.properties = []
        return user

    async def test_list_users(self, admin_client, mock_db):
        users = [self._make_mock_user(name="User A"), self._make_mock_user(name="User B")]

        with patch("app.api.v1.admin.user_service") as mock_svc:
            mock_svc.list_users = AsyncMock(return_value=users)

            resp = await admin_client.get("/api/v1/admin/users")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 2

    async def test_create_user(self, admin_client, mock_db):
        new_user = self._make_mock_user(name="New Employee", role="operator")

        with patch("app.api.v1.admin.user_service") as mock_svc:
            mock_svc.create_user = AsyncMock(return_value=new_user)

            resp = await admin_client.post("/api/v1/admin/users", json={
                "clerk_id": "clerk_new",
                "email": "new@test.com",
                "name": "New Employee",
                "role": "operator",
                "property_ids": [],
            })

        assert resp.status_code == 201
        data = resp.json()["data"]
        assert data["name"] == "New Employee"
        assert data["role"] == "operator"

    async def test_update_user(self, admin_client, mock_db):
        existing = self._make_mock_user(user_id=USER_ID, name="Updated Name", role="executive")

        with patch("app.api.v1.admin.user_service") as mock_svc:
            mock_svc.get_user = AsyncMock(return_value=existing)
            mock_svc.update_user = AsyncMock(return_value=existing)

            resp = await admin_client.put(f"/api/v1/admin/users/{USER_ID}", json={
                "name": "Updated Name",
                "role": "executive",
            })

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["name"] == "Updated Name"

    async def test_update_nonexistent_user(self, admin_client, mock_db):
        fake_id = uuid.uuid4()

        with patch("app.api.v1.admin.user_service") as mock_svc:
            mock_svc.get_user = AsyncMock(return_value=None)

            resp = await admin_client.put(f"/api/v1/admin/users/{fake_id}", json={
                "name": "Does Not Exist",
            })

        assert resp.status_code == 404

    async def test_delete_user(self, admin_client, mock_db):
        existing = self._make_mock_user(user_id=USER_ID)

        with patch("app.api.v1.admin.user_service") as mock_svc:
            mock_svc.get_user = AsyncMock(return_value=existing)
            mock_svc.delete_user = AsyncMock()

            resp = await admin_client.delete(f"/api/v1/admin/users/{USER_ID}")

        assert resp.status_code == 204

    async def test_delete_nonexistent_user(self, admin_client, mock_db):
        fake_id = uuid.uuid4()

        with patch("app.api.v1.admin.user_service") as mock_svc:
            mock_svc.get_user = AsyncMock(return_value=None)

            resp = await admin_client.delete(f"/api/v1/admin/users/{fake_id}")

        assert resp.status_code == 404
