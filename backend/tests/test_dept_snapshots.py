"""Tests for the DashboardService — Department Snapshot Cards."""

import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.dashboard_service import DashboardService
from tests.conftest import PROPERTY_ID


class TestGetDeptSnapshots:
    """Test DashboardService.get_dept_snapshots card generation and KPI calculations."""

    @pytest.fixture
    def service(self):
        return DashboardService()

    def _mock_row(self, code: str, value: float):
        row = MagicMock()
        row.code = code
        row.value = value
        return row

    def _setup_db(self, mock_db, actuals_rows, budget_rows):
        """Set up mock_db.execute for the 2 queries (range actuals + prorated budget)."""
        results = []
        for rows in [actuals_rows, budget_rows]:
            result = MagicMock()
            result.fetchall.return_value = rows
            results.append(result)
        mock_db.execute = AsyncMock(side_effect=results)

    async def test_returns_six_department_cards(self, service, mock_db):
        self._setup_db(mock_db, [], [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        assert result.property_id == PROPERTY_ID
        assert result.property_name == "Test Hotel"
        assert result.period == "mtd"
        assert len(result.cards) == 6

        names = [c.dept_name for c in result.cards]
        assert names == ["Rooms", "F&B", "Golf", "Mountain Ops", "Spa", "Retail"]

    async def test_correct_kpi_labels(self, service, mock_db):
        self._setup_db(mock_db, [], [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        labels = {c.dept_name: (c.kpi1_label, c.kpi2_label) for c in result.cards}
        assert labels["Rooms"] == ("Margin %", "Labor %")
        assert labels["F&B"] == ("Food Cost %", "Labor %")
        assert labels["Golf"] == ("Rounds", "Rev/Round")
        assert labels["Mountain Ops"] == ("Skier Visits", "Rev/Visit")
        assert labels["Spa"] == ("Treatments", "Rev/Treatment")
        assert labels["Retail"] == ("Margin %", "Labor %")

    async def test_department_with_no_data_has_data_false(self, service, mock_db):
        """Departments with zero revenue and zero expense should have has_data=False."""
        self._setup_db(mock_db, [], [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        for card in result.cards:
            assert card.has_data is False
            assert card.revenue == 0
            assert card.budget == 0

    async def test_rooms_has_data_true_with_revenue(self, service, mock_db):
        actuals = [
            self._mock_row("room_revenue", 500_000_00),
            self._mock_row("other_room_revenue", 20_000_00),
            self._mock_row("rooms_labor", 80_000_00),
            self._mock_row("rooms_ota_commissions", 30_000_00),
            self._mock_row("rooms_supplies", 10_000_00),
            self._mock_row("rooms_other_expense", 5_000_00),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rooms = next(c for c in result.cards if c.dept_name == "Rooms")
        assert rooms.has_data is True
        assert rooms.revenue == 520_000_00  # 500k + 20k

    async def test_rooms_margin_pct(self, service, mock_db):
        """Rooms Margin % = (revenue - expenses) / revenue * 100."""
        actuals = [
            self._mock_row("room_revenue", 100_000),
            self._mock_row("rooms_labor", 20_000),
            self._mock_row("rooms_ota_commissions", 10_000),
            self._mock_row("rooms_supplies", 5_000),
            self._mock_row("rooms_other_expense", 5_000),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rooms = next(c for c in result.cards if c.dept_name == "Rooms")
        # revenue = 100_000, expenses = 40_000, margin = 60%
        assert rooms.kpi1_value == "60.0%"

    async def test_rooms_labor_pct(self, service, mock_db):
        """Rooms Labor % = rooms_labor / revenue * 100."""
        actuals = [
            self._mock_row("room_revenue", 100_000),
            self._mock_row("rooms_labor", 25_000),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rooms = next(c for c in result.cards if c.dept_name == "Rooms")
        assert rooms.kpi2_value == "25.0%"

    async def test_fb_food_cost_pct(self, service, mock_db):
        """F&B Food Cost % = fb_cost_of_sales / total_fb_revenue * 100."""
        actuals = [
            self._mock_row("food_revenue", 200_000),
            self._mock_row("beverage_revenue", 80_000),
            self._mock_row("catering_revenue", 20_000),
            self._mock_row("fb_cost_of_sales", 75_000),
            self._mock_row("fb_labor", 60_000),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        fb = next(c for c in result.cards if c.dept_name == "F&B")
        # revenue = 300_000, food cost = 75_000 → 25.0%
        assert fb.kpi1_value == "25.0%"

    async def test_fb_labor_pct(self, service, mock_db):
        """F&B Labor % = fb_labor / total_fb_revenue * 100."""
        actuals = [
            self._mock_row("food_revenue", 200_000),
            self._mock_row("beverage_revenue", 100_000),
            self._mock_row("fb_labor", 90_000),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        fb = next(c for c in result.cards if c.dept_name == "F&B")
        # revenue = 300_000, labor = 90_000 → 30.0%
        assert fb.kpi2_value == "30.0%"

    async def test_golf_rounds_count(self, service, mock_db):
        """Golf Rounds = golf_rounds line item count."""
        actuals = [
            self._mock_row("golf_greens_revenue", 50_000_00),
            self._mock_row("golf_rounds", 500),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        golf = next(c for c in result.cards if c.dept_name == "Golf")
        assert golf.kpi1_value == "500"

    async def test_golf_rev_per_round(self, service, mock_db):
        """Golf Rev/Round = total_golf_revenue / golf_rounds (in dollars)."""
        actuals = [
            self._mock_row("golf_greens_revenue", 100_000_00),  # $1000 * 100 rounds
            self._mock_row("golf_cart_revenue", 25_000_00),
            self._mock_row("golf_pro_shop_revenue", 0),
            self._mock_row("golf_rounds", 500),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        golf = next(c for c in result.cards if c.dept_name == "Golf")
        # revenue = 125_000_00 cents, rounds = 500 → $250/round
        assert golf.kpi2_value == "$250"

    async def test_spa_treatments_count(self, service, mock_db):
        actuals = [
            self._mock_row("spa_services_revenue", 30_000_00),
            self._mock_row("spa_treatments", 200),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        spa = next(c for c in result.cards if c.dept_name == "Spa")
        assert spa.kpi1_value == "200"

    async def test_spa_rev_per_treatment(self, service, mock_db):
        actuals = [
            self._mock_row("spa_services_revenue", 40_000_00),
            self._mock_row("spa_retail_revenue", 10_000_00),
            self._mock_row("spa_treatments", 250),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        spa = next(c for c in result.cards if c.dept_name == "Spa")
        # revenue = 50_000_00 cents, treatments = 250 → $200/treatment
        assert spa.kpi2_value == "$200"

    async def test_mountain_ops_skier_visits(self, service, mock_db):
        actuals = [
            self._mock_row("mountain_lift_revenue", 200_000_00),
            self._mock_row("mountain_skier_visits", 3000),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        mtn = next(c for c in result.cards if c.dept_name == "Mountain Ops")
        assert mtn.kpi1_value == "3,000"

    async def test_mountain_ops_rev_per_visit(self, service, mock_db):
        actuals = [
            self._mock_row("mountain_lift_revenue", 150_000_00),
            self._mock_row("mountain_other_revenue", 50_000_00),
            self._mock_row("mountain_skier_visits", 2000),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        mtn = next(c for c in result.cards if c.dept_name == "Mountain Ops")
        # revenue = 200_000_00 cents, visits = 2000 → $100/visit
        assert mtn.kpi2_value == "$100"

    async def test_variance_pct_calculation(self, service, mock_db):
        """Variance % = (revenue - budget) / budget * 100."""
        actuals = [
            self._mock_row("room_revenue", 110_000),
        ]
        # March 2026 = 31 days, target=22 → elapsed=22
        # prorated budget = value * 22 / 31
        # We want budget_revenue ~100_000 after proration
        # So monthly value = 100_000 * 31 / 22 ≈ 140909
        budget = [
            self._mock_row("room_revenue", 140_909),
        ]
        self._setup_db(mock_db, actuals, budget)

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rooms = next(c for c in result.cards if c.dept_name == "Rooms")
        # budget_revenue ≈ 140_909 * 22 / 31 ≈ 99,999.6
        # variance_pct ≈ (110_000 - 99_999.6) / 99_999.6 * 100 ≈ 10.0%
        assert rooms.variance_pct is not None
        assert rooms.variance_pct == pytest.approx(10.0, abs=0.2)

    async def test_variance_pct_none_when_no_budget(self, service, mock_db):
        actuals = [self._mock_row("room_revenue", 100_000)]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rooms = next(c for c in result.cards if c.dept_name == "Rooms")
        assert rooms.variance_pct is None

    async def test_zero_revenue_kpis_return_zero(self, service, mock_db):
        """When revenue is 0, percentage KPIs should show 0.0%, not crash."""
        self._setup_db(mock_db, [], [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rooms = next(c for c in result.cards if c.dept_name == "Rooms")
        assert rooms.kpi1_value == "0.0%"
        assert rooms.kpi2_value == "0.0%"

    async def test_zero_count_rev_per_unit_returns_zero(self, service, mock_db):
        """When count is 0, rev/unit KPIs should show $0, not crash."""
        actuals = [self._mock_row("golf_greens_revenue", 50_000_00)]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        golf = next(c for c in result.cards if c.dept_name == "Golf")
        assert golf.kpi2_value == "$0"

    async def test_has_data_true_with_expenses_only(self, service, mock_db):
        """Department with expenses but no revenue should still have has_data=True."""
        actuals = [self._mock_row("rooms_labor", 50_000)]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        rooms = next(c for c in result.cards if c.dept_name == "Rooms")
        assert rooms.has_data is True

    async def test_has_data_true_with_count_only(self, service, mock_db):
        """Department with only count data (no revenue/expenses) should have has_data=True."""
        actuals = [self._mock_row("golf_rounds", 150)]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        golf = next(c for c in result.cards if c.dept_name == "Golf")
        assert golf.has_data is True
        assert golf.revenue == 0

    async def test_retail_margin_pct(self, service, mock_db):
        actuals = [
            self._mock_row("retail_revenue", 80_000),
            self._mock_row("retail_labor", 15_000),
            self._mock_row("retail_cost_of_sales", 40_000),
            self._mock_row("retail_other_expense", 5_000),
        ]
        self._setup_db(mock_db, actuals, [])

        result = await service.get_dept_snapshots(
            mock_db, PROPERTY_ID, "Test Hotel", target_date=date(2026, 3, 22),
        )

        retail = next(c for c in result.cards if c.dept_name == "Retail")
        # revenue = 80_000, expenses = 60_000, margin = 25.0%
        assert retail.kpi1_value == "25.0%"
        # labor % = 15_000 / 80_000 * 100 = 18.75%
        assert retail.kpi2_value == "18.8%"
