"""Tests for DashboardService.get_mtd_pace — MTD Pace calculations."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.dashboard_service import DashboardService
from tests.conftest import PROPERTY_ID


class TestGetMTDPace:
    """Test DashboardService.get_mtd_pace calculations."""

    @pytest.fixture
    def service(self):
        return DashboardService()

    def _mock_row(self, code: str, value: float):
        row = MagicMock()
        row.code = code
        row.value = value
        return row

    def _setup_db(self, mock_db, actuals_rows, stly_rows, budget_rows, forecast_rows):
        """Set up mock_db.execute to return different results for the 4 queries."""
        results = []
        for rows in [actuals_rows, stly_rows, budget_rows, forecast_rows]:
            result = MagicMock()
            result.fetchall.return_value = rows
            results.append(result)
        mock_db.execute = AsyncMock(side_effect=results)

    async def test_returns_seven_rows(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 500_000),
            self._mock_row("rooms_sold", 1600),
            self._mock_row("available_rooms", 2200),
            self._mock_row("total_revenue", 800_000),
            self._mock_row("rooms_labor", 50_000),
            self._mock_row("fb_labor", 30_000),
        ]
        self._setup_db(mock_db, actuals, [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        assert result.property_id == PROPERTY_ID
        assert result.property_name == "Test Hotel"
        assert result.period_start == date(2026, 3, 1)
        assert result.period_end == date(2026, 3, 22)
        assert len(result.rows) == 7

        names = [r.metric_name for r in result.rows]
        assert names == [
            "Occupancy", "ADR", "RevPAR", "Room Revenue",
            "Total Revenue", "Total Labor", "Labor % of Revenue",
        ]

    async def test_days_elapsed_and_days_in_month(self, service, mock_db):
        self._setup_db(mock_db, [], [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        # March 1 to March 22 = 22 days elapsed
        assert result.days_elapsed == 22
        assert result.days_in_month == 31

    async def test_days_elapsed_first_of_month(self, service, mock_db):
        self._setup_db(mock_db, [], [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 2, 1),
        )

        assert result.days_elapsed == 1
        assert result.days_in_month == 28

    async def test_occupancy_calculation(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 100_000),
            self._mock_row("rooms_sold", 1500),
            self._mock_row("available_rooms", 2000),
            self._mock_row("total_revenue", 150_000),
        ]
        self._setup_db(mock_db, actuals, [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        occ = next(r for r in result.rows if r.metric_name == "Occupancy")
        assert occ.actual == 0.75  # 1500 / 2000
        assert occ.unit == "percentage"

    async def test_adr_calculation(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 300_000),
            self._mock_row("rooms_sold", 1500),
            self._mock_row("available_rooms", 2000),
            self._mock_row("total_revenue", 400_000),
        ]
        self._setup_db(mock_db, actuals, [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        adr = next(r for r in result.rows if r.metric_name == "ADR")
        assert adr.actual == 200.0  # 300000 / 1500
        assert adr.unit == "currency"

    async def test_revpar_calculation(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 300_000),
            self._mock_row("rooms_sold", 1500),
            self._mock_row("available_rooms", 2000),
            self._mock_row("total_revenue", 400_000),
        ]
        self._setup_db(mock_db, actuals, [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        revpar = next(r for r in result.rows if r.metric_name == "RevPAR")
        assert revpar.actual == 150.0  # 300000 / 2000
        assert revpar.unit == "currency"

    async def test_labor_pct_of_revenue(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 300_000),
            self._mock_row("rooms_sold", 1500),
            self._mock_row("available_rooms", 2000),
            self._mock_row("total_revenue", 1_000_000),
            self._mock_row("rooms_labor", 150_000),
            self._mock_row("fb_labor", 100_000),
        ]
        self._setup_db(mock_db, actuals, [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        labor_pct = next(r for r in result.rows if r.metric_name == "Labor % of Revenue")
        assert labor_pct.actual == pytest.approx(0.25)  # 250000 / 1000000
        assert labor_pct.unit == "percentage"

    async def test_labor_pct_zero_revenue(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 0),
            self._mock_row("rooms_sold", 0),
            self._mock_row("available_rooms", 0),
            self._mock_row("total_revenue", 0),
            self._mock_row("rooms_labor", 5000),
        ]
        self._setup_db(mock_db, actuals, [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        labor_pct = next(r for r in result.rows if r.metric_name == "Labor % of Revenue")
        assert labor_pct.actual == 0.0

    async def test_budget_proration(self, service, mock_db):
        """Budget should be prorated: monthly_value * days_elapsed / days_in_month."""
        actuals = [
            self._mock_row("room_revenue", 220_000),
            self._mock_row("rooms_sold", 1100),
            self._mock_row("available_rooms", 2200),
            self._mock_row("total_revenue", 350_000),
        ]
        # Monthly budget: 310_000 room_rev. Prorated for 22/31 days = 220_000
        budget = [
            self._mock_row("room_revenue", 310_000),
            self._mock_row("rooms_sold", 1550),
            self._mock_row("available_rooms", 3100),
            self._mock_row("total_revenue", 496_428),
        ]
        self._setup_db(mock_db, actuals, [], budget, [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rev = next(r for r in result.rows if r.metric_name == "Room Revenue")
        expected_budget = 310_000 * 22 / 31
        assert rev.budget == pytest.approx(expected_budget, rel=0.01)

    async def test_variance_calculations(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 250_000),
            self._mock_row("rooms_sold", 1200),
            self._mock_row("available_rooms", 2000),
            self._mock_row("total_revenue", 400_000),
        ]
        stly = [
            self._mock_row("room_revenue", 200_000),
            self._mock_row("rooms_sold", 1000),
            self._mock_row("available_rooms", 2000),
            self._mock_row("total_revenue", 320_000),
        ]
        self._setup_db(mock_db, actuals, stly, [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rev = next(r for r in result.rows if r.metric_name == "Room Revenue")
        assert rev.vs_stly == 50_000  # 250000 - 200000
        assert rev.vs_stly_pct == pytest.approx(25.0, abs=0.1)

    async def test_forecast_lock_variance(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 250_000),
            self._mock_row("rooms_sold", 1200),
            self._mock_row("available_rooms", 2000),
            self._mock_row("total_revenue", 400_000),
        ]
        # Monthly forecast: 310_000 room_rev. Prorated 22/31 = ~220_000
        forecast = [
            self._mock_row("room_revenue", 310_000),
            self._mock_row("rooms_sold", 1550),
            self._mock_row("available_rooms", 3100),
            self._mock_row("total_revenue", 496_428),
        ]
        self._setup_db(mock_db, actuals, [], [], forecast)

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rev = next(r for r in result.rows if r.metric_name == "Room Revenue")
        expected_fcst = 310_000 * 22 / 31
        assert rev.vs_forecast == pytest.approx(250_000 - expected_fcst, rel=0.01)

    async def test_zero_division_safe(self, service, mock_db):
        """All zeros should produce rows without division errors."""
        self._setup_db(mock_db, [], [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        assert len(result.rows) == 7
        for row in result.rows:
            assert row.actual == 0.0

    async def test_variance_pct_none_when_comparison_zero(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 100_000),
            self._mock_row("rooms_sold", 500),
            self._mock_row("available_rooms", 1000),
            self._mock_row("total_revenue", 150_000),
        ]
        self._setup_db(mock_db, actuals, [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rev = next(r for r in result.rows if r.metric_name == "Room Revenue")
        assert rev.vs_budget_pct is None
        assert rev.vs_stly_pct is None

    async def test_total_labor_sums_all_labor_items(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 0),
            self._mock_row("rooms_sold", 0),
            self._mock_row("available_rooms", 0),
            self._mock_row("total_revenue", 0),
            self._mock_row("rooms_labor", 40_000),
            self._mock_row("fb_labor", 30_000),
            self._mock_row("spa_labor", 10_000),
            self._mock_row("golf_labor", 5_000),
        ]
        self._setup_db(mock_db, actuals, [], [], [])

        result = await service.get_mtd_pace(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        labor = next(r for r in result.rows if r.metric_name == "Total Labor")
        assert labor.actual == 85_000  # 40000 + 30000 + 10000 + 5000

    async def test_defaults_to_yesterday(self, service, mock_db):
        self._setup_db(mock_db, [], [], [], [])

        result = await service.get_mtd_pace(mock_db, PROPERTY_ID, "Test Hotel")

        from datetime import timedelta
        expected = date.today() - timedelta(days=1)
        assert result.period_end == expected


class TestMakePaceRow:
    def test_positive_variance(self):
        svc = DashboardService()
        row = svc._make_pace_row("Room Revenue", 100, 80, 70, 90, "currency")
        assert row.vs_budget == 20
        assert row.vs_stly == 30
        assert row.vs_forecast == 10
        assert row.vs_budget_pct == 25.0
        assert row.vs_stly_pct == pytest.approx(42.9, abs=0.1)

    def test_negative_variance(self):
        svc = DashboardService()
        row = svc._make_pace_row("Room Revenue", 80, 100, 90, 95, "currency")
        assert row.vs_budget == -20
        assert row.vs_stly == -10
        assert row.vs_forecast == -15

    def test_zero_comparisons(self):
        svc = DashboardService()
        row = svc._make_pace_row("Room Revenue", 100, 0, 0, 0, "currency")
        assert row.vs_budget_pct is None
        assert row.vs_stly_pct is None
