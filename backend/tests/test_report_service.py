"""Tests for the ReportService business logic."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.common import TimePeriod
from app.schemas.report import InterMonthResponse, ReportLineItem
from app.services.report_service import ReportService
from app.models.forecast_lock import ForecastLock

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
        svc._fetch_forecast_lock = AsyncMock(return_value={})
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


class TestForecastLock:
    """Test _fetch_forecast_lock and forecast lock integration in _build_lines."""

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

    def test_build_lines_with_no_forecast_lock(self, service):
        """forecast_lock field is None when no lock data exists."""
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        actuals = {LINE_ITEM_ID: 100000}
        budgets = {LINE_ITEM_ID: 80000}

        lines = service._build_lines(items, actuals, budgets, {}, forecast_lock={}, depth=0)
        assert lines[0].forecast_lock is None

    def test_build_lines_with_forecast_lock_value(self, service):
        """forecast_lock field is populated when lock data exists for the line item."""
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        actuals = {LINE_ITEM_ID: 100000}
        budgets = {LINE_ITEM_ID: 80000}
        fl = {LINE_ITEM_ID: 95000}

        lines = service._build_lines(items, actuals, budgets, {}, forecast_lock=fl, depth=0)
        assert lines[0].forecast_lock == 95000

    def test_build_lines_forecast_lock_none_when_omitted(self, service):
        """forecast_lock defaults to None when forecast_lock dict is not passed."""
        items = [self._make_line_item(LINE_ITEM_ID, "room_revenue", "Room Revenue")]
        lines = service._build_lines(items, {LINE_ITEM_ID: 100000}, {}, {}, depth=0)
        assert lines[0].forecast_lock is None

    async def test_fetch_forecast_lock_empty_when_no_locks(self, service, mock_db):
        """_fetch_forecast_lock returns empty dict when no locks exist."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service._fetch_forecast_lock(
            mock_db, PROPERTY_ID, date(2026, 3, 1), date(2026, 3, 23),
        )
        assert result == {}

    async def test_fetch_forecast_lock_prorates_partial_month(self, service, mock_db):
        """_fetch_forecast_lock prorates values for partial month coverage."""
        mock_row = MagicMock()
        mock_row.line_item_id = LINE_ITEM_ID
        mock_row.year = 2026
        mock_row.month = 3
        mock_row.value = 310000  # $3100 for 31-day month -> $100/day

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute = AsyncMock(return_value=mock_result)

        # 10 days of a 31-day month
        result = await service._fetch_forecast_lock(
            mock_db, PROPERTY_ID, date(2026, 3, 1), date(2026, 3, 10),
        )
        expected = int(310000 * 10 / 31)
        assert result[LINE_ITEM_ID] == expected

    async def test_get_inter_month_includes_forecast_lock(self, mock_db):
        """get_inter_month passes forecast lock data through to _build_lines."""
        svc = ReportService()
        svc._fetch_actuals = AsyncMock(return_value={LINE_ITEM_ID: 100000})
        svc._fetch_budget_data = AsyncMock(return_value={LINE_ITEM_ID: 80000})
        svc._fetch_prior_year = AsyncMock(return_value={})
        svc._fetch_forecast_lock = AsyncMock(return_value={LINE_ITEM_ID: 90000})
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

        result = await svc.get_inter_month(
            db=mock_db,
            property_id=PROPERTY_ID,
            property_name="Test Hotel",
            period="mtd",
            start_date=None,
            end_date=None,
            cache=None,
            tenant_id=TENANT_ID,
        )

        assert result.lines[0].forecast_lock == 90000


class TestTimePeriodFetchMethods:
    """Test _fetch_daily_single, _fetch_rest_of_year, and _fetch_annual."""

    @pytest.fixture
    def service(self):
        return ReportService()

    async def test_fetch_daily_single_returns_records_for_one_date(self, service, mock_db):
        """_fetch_daily_single returns {line_item_id: value} for a single date."""
        mock_row = MagicMock()
        mock_row.line_item_id = LINE_ITEM_ID
        mock_row.actual_value = 5000

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service._fetch_daily_single(mock_db, PROPERTY_ID, date(2026, 3, 22))

        assert result == {LINE_ITEM_ID: 5000}
        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params["target_date"] == date(2026, 3, 22)
        assert params["property_id"] == PROPERTY_ID

    async def test_fetch_daily_single_empty_when_no_data(self, service, mock_db):
        """_fetch_daily_single returns empty dict when no records exist."""
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service._fetch_daily_single(mock_db, PROPERTY_ID, date(2026, 3, 22))
        assert result == {}

    @patch("app.services.report_service.date")
    async def test_fetch_rest_of_year_returns_forecast_for_remaining_months(
        self, mock_date, service, mock_db,
    ):
        """_fetch_rest_of_year sums forecast_locks for months after current."""
        mock_date.today.return_value = date(2026, 3, 23)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        row1 = MagicMock()
        row1.line_item_id = LINE_ITEM_ID
        row1.actual_value = 270000  # sum of Apr-Dec forecast

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [row1]
        mock_db.execute = AsyncMock(return_value=mock_result)

        result = await service._fetch_rest_of_year(mock_db, PROPERTY_ID)

        assert result == {LINE_ITEM_ID: 270000}
        call_args = mock_db.execute.call_args
        params = call_args[0][1]
        assert params["start_month"] == 4
        assert params["year"] == 2026

    @patch("app.services.report_service.date")
    async def test_fetch_rest_of_year_empty_in_december(self, mock_date, service, mock_db):
        """_fetch_rest_of_year returns empty dict when current month is December."""
        mock_date.today.return_value = date(2026, 12, 15)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        result = await service._fetch_rest_of_year(mock_db, PROPERTY_ID)
        assert result == {}

    @patch("app.services.report_service.date")
    async def test_fetch_annual_combines_ytd_and_rest_of_year(self, mock_date, service, mock_db):
        """_fetch_annual merges YTD actuals with rest-of-year forecast."""
        mock_date.today.return_value = date(2026, 3, 23)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        # First call: YTD actuals query
        ytd_row = MagicMock()
        ytd_row.line_item_id = LINE_ITEM_ID
        ytd_row.actual_value = 100000
        ytd_result = MagicMock()
        ytd_result.fetchall.return_value = [ytd_row]

        # Second call: rest_of_year forecast query
        rest_row = MagicMock()
        rest_row.line_item_id = LINE_ITEM_ID
        rest_row.actual_value = 200000
        rest_result = MagicMock()
        rest_result.fetchall.return_value = [rest_row]

        mock_db.execute = AsyncMock(side_effect=[ytd_result, rest_result])

        result = await service._fetch_annual(mock_db, PROPERTY_ID)

        # Should combine: 100000 (ytd) + 200000 (rest) = 300000
        assert result[LINE_ITEM_ID] == 300000

    @patch("app.services.report_service.date")
    async def test_fetch_annual_ytd_only_when_no_forecast(self, mock_date, service, mock_db):
        """_fetch_annual returns just YTD when no remaining forecast exists."""
        mock_date.today.return_value = date(2026, 12, 20)
        mock_date.side_effect = lambda *args, **kw: date(*args, **kw)

        ytd_row = MagicMock()
        ytd_row.line_item_id = LINE_ITEM_ID
        ytd_row.actual_value = 500000
        ytd_result = MagicMock()
        ytd_result.fetchall.return_value = [ytd_row]

        mock_db.execute = AsyncMock(return_value=ytd_result)

        result = await service._fetch_annual(mock_db, PROPERTY_ID)
        assert result[LINE_ITEM_ID] == 500000
