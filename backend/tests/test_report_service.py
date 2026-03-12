"""Tests for the ReportService business logic."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.report import InterMonthResponse, ReportLineItem
from app.services.report_service import ReportService

from tests.conftest import LINE_ITEM_ID, LINE_ITEM_ID_2, PARENT_LINE_ITEM_ID, PROPERTY_ID, TENANT_ID


class TestBuildLines:
    """Test _build_lines variance calculations (pure logic)."""

    def _make_line_item(self, id, code, name, data_type="revenue", is_summary=True, sort_order=0, parent_id=None):
        item = MagicMock()
        item.id = id
        item.code = code
        item.name = name
        item.data_type = data_type
        item.is_summary = is_summary
        item.sort_order = sort_order
        item.parent_id = parent_id
        return item

    @pytest.fixture
    def service(self):
        return ReportService()

    def test_basic_variance(self, service):
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        actuals = {LINE_ITEM_ID: 100000}  # $1000
        budgets = {LINE_ITEM_ID: 80000}   # $800
        prior_year = {}

        lines = service._build_lines(items, actuals, budgets, prior_year, depth=0)

        assert len(lines) == 1
        line = lines[0]
        assert line.actual == 100000
        assert line.budget == 80000
        assert line.variance_dollars == 20000  # $200 favorable
        assert line.variance_pct == 25.0  # 25%

    def test_negative_variance(self, service):
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        actuals = {LINE_ITEM_ID: 50000}
        budgets = {LINE_ITEM_ID: 80000}
        prior_year = {}

        lines = service._build_lines(items, actuals, budgets, prior_year, depth=0)

        line = lines[0]
        assert line.variance_dollars == -30000
        assert line.variance_pct == -37.5

    def test_zero_budget_variance_pct_is_none(self, service):
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        actuals = {LINE_ITEM_ID: 100000}
        budgets = {LINE_ITEM_ID: 0}
        prior_year = {}

        lines = service._build_lines(items, actuals, budgets, prior_year, depth=0)
        assert lines[0].variance_pct is None

    def test_missing_actual_defaults_to_zero(self, service):
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        actuals = {}  # No data for this line item
        budgets = {LINE_ITEM_ID: 80000}
        prior_year = {}

        lines = service._build_lines(items, actuals, budgets, prior_year, depth=0)
        assert lines[0].actual == 0
        assert lines[0].variance_dollars == -80000

    def test_missing_budget_defaults_to_zero(self, service):
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        actuals = {LINE_ITEM_ID: 100000}
        budgets = {}
        prior_year = {}

        lines = service._build_lines(items, actuals, budgets, prior_year, depth=0)
        assert lines[0].budget == 0
        assert lines[0].variance_dollars == 100000

    def test_prior_year_variance(self, service):
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        actuals = {LINE_ITEM_ID: 110000}
        budgets = {LINE_ITEM_ID: 100000}
        prior_year = {LINE_ITEM_ID: 100000}

        lines = service._build_lines(items, actuals, budgets, prior_year, depth=0)

        line = lines[0]
        assert line.prior_year_actual == 100000
        assert line.py_variance_dollars == 10000
        assert line.py_variance_pct == 10.0

    def test_no_prior_year_data(self, service):
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        actuals = {LINE_ITEM_ID: 100000}
        budgets = {LINE_ITEM_ID: 80000}
        prior_year = {}  # No PY data

        lines = service._build_lines(items, actuals, budgets, prior_year, depth=0)

        line = lines[0]
        assert line.prior_year_actual is None
        assert line.py_variance_dollars is None
        assert line.py_variance_pct is None

    def test_zero_prior_year_pct_is_none(self, service):
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        actuals = {LINE_ITEM_ID: 100000}
        budgets = {LINE_ITEM_ID: 80000}
        prior_year = {LINE_ITEM_ID: 0}

        lines = service._build_lines(items, actuals, budgets, prior_year, depth=0)
        assert lines[0].py_variance_pct is None

    def test_multiple_line_items(self, service):
        items = [
            self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue", sort_order=1),
            self._make_line_item(LINE_ITEM_ID_2, "fb_total", "F&B Revenue", sort_order=2),
        ]
        actuals = {LINE_ITEM_ID: 100000, LINE_ITEM_ID_2: 50000}
        budgets = {LINE_ITEM_ID: 90000, LINE_ITEM_ID_2: 60000}
        prior_year = {}

        lines = service._build_lines(items, actuals, budgets, prior_year, depth=0)
        assert len(lines) == 2
        assert lines[0].code == "room_revenue"
        assert lines[1].code == "fb_total"

    def test_depth_is_set(self, service):
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        lines = service._build_lines(items, {}, {}, {}, depth=2)
        assert lines[0].depth == 2

    def test_line_item_fields_propagated(self, service):
        items = [self._make_line_item(
            LINE_ITEM_ID, "room_revenue", "Room Revenue",
            data_type="revenue", is_summary=True, sort_order=5, parent_id=PARENT_LINE_ITEM_ID,
        )]
        lines = service._build_lines(items, {}, {}, {}, depth=0)

        line = lines[0]
        assert line.id == LINE_ITEM_ID
        assert line.code == "room_revenue"
        assert line.name == "Room Revenue"
        assert line.data_type == "revenue"
        assert line.is_summary is True
        assert line.sort_order == 5
        assert line.parent_id == PARENT_LINE_ITEM_ID


class TestGetInterMonth:
    """Test get_inter_month orchestration."""

    @pytest.fixture
    def service(self):
        svc = ReportService()
        svc._fetch_actuals = AsyncMock(return_value={LINE_ITEM_ID: 100000})
        svc._fetch_budget_data = AsyncMock(return_value={LINE_ITEM_ID: 80000})
        svc._fetch_prior_year = AsyncMock(return_value={LINE_ITEM_ID: 90000})
        # Mock rollup to pass through (leaf data already keyed by correct IDs)
        svc._rollup_to_summaries = AsyncMock(side_effect=lambda db, data: data)

        mock_item = MagicMock()
        mock_item.id = LINE_ITEM_ID
        mock_item.code = "room_revenue"
        mock_item.name = "Room Revenue"
        mock_item.data_type = "revenue"
        mock_item.is_summary = True
        mock_item.sort_order = 1
        mock_item.parent_id = None
        svc._fetch_line_items = AsyncMock(return_value=[mock_item])
        return svc

    async def test_returns_inter_month_response(self, service, mock_db):
        result = await service.get_inter_month(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            period="mtd",
            start_date=None,
            end_date=None,
            cache=None,
            tenant_id=TENANT_ID,
        )

        assert isinstance(result, InterMonthResponse)
        assert result.property_id == PROPERTY_ID
        assert result.property_name == "Test Hotel"
        assert result.period == "mtd"
        assert len(result.lines) == 1
        assert result.lines[0].actual == 100000

    async def test_custom_period_uses_provided_dates(self, service, mock_db):
        result = await service.get_inter_month(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            period="custom",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 31),
            cache=None,
            tenant_id=TENANT_ID,
        )

        assert result.start_date == date(2026, 1, 1)
        assert result.end_date == date(2026, 1, 31)

    async def test_caches_result(self, service, mock_db):
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=None)
        cache.set = AsyncMock()

        await service.get_inter_month(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            period="mtd",
            start_date=None,
            end_date=None,
            cache=cache,
            tenant_id=TENANT_ID,
        )

        cache.set.assert_called_once()

    async def test_returns_cached_result(self, service, mock_db):
        cached_data = {
            "property_id": str(PROPERTY_ID),
            "property_name": "Cached Hotel",
            "period": "mtd",
            "start_date": "2026-03-01",
            "end_date": "2026-03-12",
            "lines": [],
        }
        cache = AsyncMock()
        cache.get = AsyncMock(return_value=cached_data)

        result = await service.get_inter_month(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            period="mtd",
            start_date=None,
            end_date=None,
            cache=cache,
            tenant_id=TENANT_ID,
        )

        assert result.property_name == "Cached Hotel"
        # DB should not have been queried
        service._fetch_actuals.assert_not_called()
