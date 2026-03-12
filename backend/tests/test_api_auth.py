"""Tests for the auth API endpoints."""

import pytest

from tests.conftest import PROPERTY_ID, USER_ID


class TestAuthMe:
    async def test_returns_current_user(self, admin_client, admin_user):
        resp = await admin_client.get("/api/v1/auth/me")
        assert resp.status_code == 200

        body = resp.json()
        assert "data" in body
        data = body["data"]
        assert data["email"] == "test@example.com"
        assert data["name"] == "Test User"
        assert data["role"] == "admin"
        assert data["is_active"] is True

    async def test_manager_can_access_me(self, manager_client, manager_user):
        resp = await manager_client.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["role"] == "manager"

    async def test_unauthenticated_returns_401(self, unauth_client):
        resp = await unauth_client.get("/api/v1/auth/me")
        assert resp.status_code == 401
