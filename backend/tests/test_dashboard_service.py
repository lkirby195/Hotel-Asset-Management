"""Tests for the DashboardService — GM Yesterday Performance."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.dashboard_service import DashboardService
from tests.conftest import PROPERTY_ID


class TestGetYesterday:
    """Test DashboardService.get_yesterday KPI calculations."""

    @pytest.fixture
    def service(self):
        return DashboardService()

    def _mock_row(self, code: str, value: float):
        row = MagicMock()
        row.code = code
        row.value = value
        return row

    def _setup_db(self, mock_db, actuals_rows, stly_rows, budget_rows):
        """Set up mock_db.execute to return different results for the 3 queries."""
        results = []
        for rows in [actuals_rows, stly_rows, budget_rows]:
            result = MagicMock()
            result.fetchall.return_value = rows
            results.append(result)
        mock_db.execute = AsyncMock(side_effect=results)

    async def test_returns_six_kpis(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 500_00),
            self._mock_row("rooms_sold", 80),
            self._mock_row("available_rooms", 100),
            self._mock_row("rooms_labor", 100_00),
            self._mock_row("fb_labor", 50_00),
        ]
        self._setup_db(mock_db, actuals, [], [])

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        assert result.property_id == PROPERTY_ID
        assert result.property_name == "Test Hotel"
        assert result.date == date(2026, 3, 22)
        assert len(result.kpis) == 6

        names = [k.metric_name for k in result.kpis]
        assert names == ["Rooms Sold", "Occupancy", "ADR", "RevPAR", "Room Revenue", "Total Labor"]

    async def test_occupancy_calculation(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 10000),
            self._mock_row("rooms_sold", 75),
            self._mock_row("available_rooms", 100),
        ]
        self._setup_db(mock_db, actuals, [], [])

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        occ = next(k for k in result.kpis if k.metric_name == "Occupancy")
        assert occ.actual == 0.75

    async def test_adr_calculation(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 15000),
            self._mock_row("rooms_sold", 50),
            self._mock_row("available_rooms", 100),
        ]
        self._setup_db(mock_db, actuals, [], [])

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        adr = next(k for k in result.kpis if k.metric_name == "ADR")
        assert adr.actual == 300.0  # 15000 / 50

    async def test_revpar_calculation(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 20000),
            self._mock_row("rooms_sold", 80),
            self._mock_row("available_rooms", 100),
        ]
        self._setup_db(mock_db, actuals, [], [])

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        revpar = next(k for k in result.kpis if k.metric_name == "RevPAR")
        assert revpar.actual == 200.0  # 20000 / 100

    async def test_stly_variance(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 10000),
            self._mock_row("rooms_sold", 80),
            self._mock_row("available_rooms", 100),
        ]
        stly = [
            self._mock_row("room_revenue", 8000),
            self._mock_row("rooms_sold", 70),
            self._mock_row("available_rooms", 100),
        ]
        self._setup_db(mock_db, actuals, stly, [])

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rooms = next(k for k in result.kpis if k.metric_name == "Rooms Sold")
        assert rooms.variance_stly == 10  # 80 - 70
        assert rooms.variance_stly_pct == pytest.approx(14.3, abs=0.1)

        rev = next(k for k in result.kpis if k.metric_name == "Room Revenue")
        assert rev.variance_stly == 2000  # 10000 - 8000

    async def test_budget_variance(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 10000),
            self._mock_row("rooms_sold", 80),
            self._mock_row("available_rooms", 100),
        ]
        # March 2026 has 31 days, budget prorated = value / 31
        budget = [
            self._mock_row("room_revenue", 310000),  # 310000/31 = 10000/day
            self._mock_row("rooms_sold", 2480),       # 2480/31 = 80/day
            self._mock_row("available_rooms", 3100),   # 3100/31 = 100/day
        ]
        self._setup_db(mock_db, actuals, [], budget)

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rev = next(k for k in result.kpis if k.metric_name == "Room Revenue")
        assert rev.variance_budget == pytest.approx(0, abs=1)

    async def test_zero_rooms_sold_no_division_error(self, service, mock_db):
        """No rooms sold should give 0 occupancy/ADR/RevPAR, not a division error."""
        actuals = [
            self._mock_row("room_revenue", 0),
            self._mock_row("rooms_sold", 0),
            self._mock_row("available_rooms", 100),
        ]
        self._setup_db(mock_db, actuals, [], [])

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        occ = next(k for k in result.kpis if k.metric_name == "Occupancy")
        assert occ.actual == 0.0

        adr = next(k for k in result.kpis if k.metric_name == "ADR")
        assert adr.actual == 0.0

        revpar = next(k for k in result.kpis if k.metric_name == "RevPAR")
        assert revpar.actual == 0.0

    async def test_zero_available_rooms_no_division_error(self, service, mock_db):
        """Zero available rooms should give 0 occupancy/RevPAR, not a division error."""
        actuals = [
            self._mock_row("room_revenue", 5000),
            self._mock_row("rooms_sold", 0),
            self._mock_row("available_rooms", 0),
        ]
        self._setup_db(mock_db, actuals, [], [])

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        occ = next(k for k in result.kpis if k.metric_name == "Occupancy")
        assert occ.actual == 0.0

        revpar = next(k for k in result.kpis if k.metric_name == "RevPAR")
        assert revpar.actual == 0.0

    async def test_missing_data_returns_zeros(self, service, mock_db):
        """No data at all should still return 6 KPIs with zeros."""
        self._setup_db(mock_db, [], [], [])

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        assert len(result.kpis) == 6
        for kpi in result.kpis:
            assert kpi.actual == 0.0

    async def test_total_labor_sums_all_labor_items(self, service, mock_db):
        actuals = [
            self._mock_row("rooms_labor", 1000),
            self._mock_row("fb_labor", 800),
            self._mock_row("spa_labor", 300),
            self._mock_row("golf_labor", 200),
            self._mock_row("room_revenue", 0),
            self._mock_row("rooms_sold", 0),
            self._mock_row("available_rooms", 0),
        ]
        self._setup_db(mock_db, actuals, [], [])

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        labor = next(k for k in result.kpis if k.metric_name == "Total Labor")
        assert labor.actual == 2300  # 1000 + 800 + 300 + 200

    async def test_variance_pct_none_when_budget_zero(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 5000),
            self._mock_row("rooms_sold", 50),
            self._mock_row("available_rooms", 100),
        ]
        self._setup_db(mock_db, actuals, [], [])

        result = await service.get_yesterday(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rev = next(k for k in result.kpis if k.metric_name == "Room Revenue")
        assert rev.variance_budget_pct is None
        assert rev.variance_stly_pct is None

    async def test_defaults_to_yesterday(self, service, mock_db):
        self._setup_db(mock_db, [], [], [])

        result = await service.get_yesterday(mock_db, PROPERTY_ID, "Test Hotel")

        from datetime import timedelta
        expected = date.today() - timedelta(days=1)
        assert result.date == expected


class TestSameDayLastYear:
    def test_normal_date(self):
        svc = DashboardService()
        assert svc._same_day_last_year(date(2026, 3, 22)) == date(2025, 3, 22)

    def test_leap_day(self):
        svc = DashboardService()
        assert svc._same_day_last_year(date(2024, 2, 29)) == date(2023, 2, 28)
