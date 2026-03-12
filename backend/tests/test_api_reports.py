"""Tests for the reports API endpoints."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.report import InterMonthResponse, ReportLineItem
from tests.conftest import LINE_ITEM_ID, PROPERTY_ID, TENANT_ID


def _make_report_response():
    return InterMonthResponse(
        property_id=PROPERTY_ID,
        property_name="Test Hotel",
        period="mtd",
        start_date=date(2026, 3, 1),
        end_date=date(2026, 3, 12),
        lines=[
            ReportLineItem(
                id=LINE_ITEM_ID,
                code="room_revenue",
                name="Room Revenue",
                parent_id=None,
                is_summary=True,
                data_type="revenue",
                sort_order=1,
                depth=0,
                actual=100000,
                budget=80000,
                variance_dollars=20000,
                variance_pct=25.0,
                prior_year_actual=90000,
                py_variance_dollars=10000,
                py_variance_pct=11.11,
            )
        ],
    )


def _make_mock_property():
    prop = MagicMock()
    prop.id = PROPERTY_ID
    prop.name = "Test Hotel"
    prop.code = "PROP1"
    prop.timezone = "America/New_York"
    prop.is_active = True
    return prop


class TestInterMonthReport:
    async def test_get_report_mtd(self, admin_client, mock_db, mock_redis):
        report = _make_report_response()

        with patch("app.api.v1.reports.property_service") as mock_ps, \
             patch("app.api.v1.reports.report_service") as mock_rs:
            mock_ps.get_property = AsyncMock(return_value=_make_mock_property())
            mock_rs.get_inter_month = AsyncMock(return_value=report)

            resp = await admin_client.get(f"/api/v1/reports/inter-month/{PROPERTY_ID}?period=mtd")

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["property_name"] == "Test Hotel"
        assert data["period"] == "mtd"
        assert len(data["lines"]) == 1
        assert data["lines"][0]["actual"] == 100000

    async def test_custom_period_requires_dates(self, admin_client, mock_db, mock_redis):
        with patch("app.api.v1.reports.property_service") as mock_ps:
            mock_ps.get_property = AsyncMock(return_value=_make_mock_property())

            resp = await admin_client.get(f"/api/v1/reports/inter-month/{PROPERTY_ID}?period=custom")

        assert resp.status_code == 400
        assert "start and end" in resp.json()["detail"].lower()

    async def test_custom_period_with_dates(self, admin_client, mock_db, mock_redis):
        report = _make_report_response()

        with patch("app.api.v1.reports.property_service") as mock_ps, \
             patch("app.api.v1.reports.report_service") as mock_rs:
            mock_ps.get_property = AsyncMock(return_value=_make_mock_property())
            mock_rs.get_inter_month = AsyncMock(return_value=report)

            resp = await admin_client.get(
                f"/api/v1/reports/inter-month/{PROPERTY_ID}?period=custom&start=2026-01-01&end=2026-01-31"
            )

        assert resp.status_code == 200

    async def test_invalid_period_rejected(self, admin_client, mock_db, mock_redis):
        resp = await admin_client.get(f"/api/v1/reports/inter-month/{PROPERTY_ID}?period=invalid")
        assert resp.status_code == 422  # Validation error

    async def test_property_not_found(self, admin_client, mock_db, mock_redis):
        with patch("app.api.v1.reports.property_service") as mock_ps:
            mock_ps.get_property = AsyncMock(return_value=None)

            resp = await admin_client.get(f"/api/v1/reports/inter-month/{PROPERTY_ID}?period=mtd")

        assert resp.status_code == 404

    async def test_manager_access_assigned_property(self, manager_client, mock_db, mock_redis):
        report = _make_report_response()

        with patch("app.api.v1.reports.property_service") as mock_ps, \
             patch("app.api.v1.reports.report_service") as mock_rs:
            mock_ps.get_property = AsyncMock(return_value=_make_mock_property())
            mock_rs.get_inter_month = AsyncMock(return_value=report)

            resp = await manager_client.get(f"/api/v1/reports/inter-month/{PROPERTY_ID}?period=mtd")

        assert resp.status_code == 200

    async def test_manager_blocked_from_unassigned_property(self, manager_client, mock_db, mock_redis):
        unassigned = uuid.UUID("00000000-0000-0000-0000-000000000099")
        resp = await manager_client.get(f"/api/v1/reports/inter-month/{unassigned}?period=mtd")
        assert resp.status_code == 403


class TestInterMonthChildren:
    async def test_get_children(self, admin_client, mock_db, mock_redis):
        parent_id = uuid.UUID("00000000-0000-0000-0000-000000003000")
        children = [
            ReportLineItem(
                id=LINE_ITEM_ID,
                code="transient_revenue",
                name="Transient Revenue",
                parent_id=parent_id,
                is_summary=False,
                data_type="revenue",
                sort_order=1,
                depth=1,
                actual=60000,
                budget=50000,
                variance_dollars=10000,
                variance_pct=20.0,
                prior_year_actual=None,
                py_variance_dollars=None,
                py_variance_pct=None,
            )
        ]

        with patch("app.api.v1.reports.report_service") as mock_rs:
            mock_rs.get_children = AsyncMock(return_value=children)

            resp = await admin_client.get(
                f"/api/v1/reports/inter-month/{PROPERTY_ID}/children/{parent_id}?period=mtd"
            )

        assert resp.status_code == 200
        data = resp.json()["data"]
        assert len(data) == 1
        assert data[0]["code"] == "transient_revenue"
        assert data[0]["depth"] == 1

    async def test_children_with_custom_period(self, admin_client, mock_db, mock_redis):
        parent_id = uuid.UUID("00000000-0000-0000-0000-000000003000")

        with patch("app.api.v1.reports.report_service") as mock_rs:
            mock_rs.get_children = AsyncMock(return_value=[])

            resp = await admin_client.get(
                f"/api/v1/reports/inter-month/{PROPERTY_ID}/children/{parent_id}"
                f"?period=custom&start=2026-01-01&end=2026-01-31"
            )

        assert resp.status_code == 200
