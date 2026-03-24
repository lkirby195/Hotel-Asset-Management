"""Tests for DashboardService.get_forward_look — Forward Look / OTB."""

import uuid
from datetime import date, timedelta
from unittest.mock import AsyncMock

import pytest

from app.adapters.mock_adapter import MockAdapter
from app.services.dashboard_service import DashboardService
from tests.conftest import PROPERTY_ID

AVAILABLE_ROOMS = 224
PROPERTY_CODE = "MOCK"


class TestGetForwardLook:
    """Test DashboardService.get_forward_look calculations."""

    @pytest.fixture
    def service(self):
        return DashboardService()

    @pytest.fixture
    def mock_db(self):
        return AsyncMock()

    @pytest.fixture
    def adapter(self):
        return MockAdapter()

    async def _call(self, service, mock_db, adapter, target_date):
        return await service.get_forward_look(
            mock_db, PROPERTY_ID, "Test Hotel",
            property_code=PROPERTY_CODE,
            available_rooms=AVAILABLE_ROOMS,
            adapter=adapter,
            target_date=target_date,
        )

    async def test_returns_three_summary_cards(self, service, mock_db, adapter):
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        assert len(result.summary_cards) == 3
        names = [c.window_name for c in result.summary_cards]
        assert names == ["Rest of Month", "Next 14 Days", "Next 30 Days"]

    async def test_returns_seven_daily_rows(self, service, mock_db, adapter):
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        assert len(result.daily_detail) == 7

    async def test_daily_dates_are_consecutive(self, service, mock_db, adapter):
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        dates = [row.date for row in result.daily_detail]
        for i in range(1, len(dates)):
            assert dates[i] == dates[i - 1] + timedelta(days=1)

    async def test_first_daily_date_matches_target(self, service, mock_db, adapter):
        target = date(2026, 3, 15)
        result = await self._call(service, mock_db, adapter, target)
        assert result.daily_detail[0].date == target

    async def test_response_metadata(self, service, mock_db, adapter):
        target = date(2026, 3, 15)
        result = await self._call(service, mock_db, adapter, target)
        assert result.property_id == PROPERTY_ID
        assert result.property_name == "Test Hotel"
        assert result.as_of_date == target
        assert result.available_rooms_per_night == AVAILABLE_ROOMS

    async def test_rest_of_month_window_dates(self, service, mock_db, adapter):
        target = date(2026, 3, 15)
        result = await self._call(service, mock_db, adapter, target)
        rom = result.summary_cards[0]
        assert rom.date_start == target
        assert rom.date_end == date(2026, 3, 31)
        assert rom.nights == 17  # Mar 15 through Mar 31

    async def test_next_14_days_window(self, service, mock_db, adapter):
        target = date(2026, 3, 15)
        result = await self._call(service, mock_db, adapter, target)
        card = result.summary_cards[1]
        assert card.window_name == "Next 14 Days"
        assert card.date_start == target
        assert card.date_end == target + timedelta(days=13)
        assert card.nights == 14

    async def test_next_30_days_window(self, service, mock_db, adapter):
        target = date(2026, 3, 15)
        result = await self._call(service, mock_db, adapter, target)
        card = result.summary_cards[2]
        assert card.window_name == "Next 30 Days"
        assert card.nights == 30

    async def test_otb_revenue_is_positive(self, service, mock_db, adapter):
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        for card in result.summary_cards:
            assert card.otb_revenue > 0
            assert card.otb_adr > 0
            assert card.otb_occupancy > 0

    async def test_daily_rooms_split(self, service, mock_db, adapter):
        """Transient + group should equal total rooms."""
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        for row in result.daily_detail:
            assert row.transient_rooms + row.group_rooms == row.total_rooms

    async def test_daily_occupancy_range(self, service, mock_db, adapter):
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        for row in result.daily_detail:
            assert 0 <= row.occupancy <= 1.0

    async def test_stly_data_populated(self, service, mock_db, adapter):
        """STLY revenue should be populated for all cards (mock data is deterministic)."""
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        for card in result.summary_cards:
            assert card.stly_revenue > 0
            assert card.vs_stly_pct is not None

    async def test_pickup_7day_is_none(self, service, mock_db, adapter):
        """Pickup is not yet implemented — all cards should have pickup_7day=None."""
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        for card in result.summary_cards:
            assert card.pickup_7day is None

    async def test_vs_stly_calculation(self, service, mock_db, adapter):
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        for card in result.summary_cards:
            assert card.vs_stly_revenue == card.otb_revenue - card.stly_revenue

    async def test_day_of_week_populated(self, service, mock_db, adapter):
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        # Mar 15, 2026 is a Sunday
        assert result.daily_detail[0].day_of_week == "Sun"
        assert result.daily_detail[1].day_of_week == "Mon"

    async def test_deterministic_results(self, service, mock_db, adapter):
        """Same inputs should produce identical results."""
        target = date(2026, 3, 15)
        r1 = await self._call(service, mock_db, adapter, target)
        r2 = await self._call(service, mock_db, adapter, target)

        assert r1.summary_cards[0].otb_revenue == r2.summary_cards[0].otb_revenue
        assert r1.daily_detail[0].revenue == r2.daily_detail[0].revenue

    async def test_adr_equals_revenue_over_rooms(self, service, mock_db, adapter):
        result = await self._call(service, mock_db, adapter, date(2026, 3, 15))
        for row in result.daily_detail:
            if row.total_rooms > 0:
                expected_adr = row.revenue // row.total_rooms
                assert row.adr == expected_adr

    async def test_end_of_month_rest_of_month_short(self, service, mock_db, adapter):
        """Rest of month at month end should have few nights."""
        target = date(2026, 3, 29)
        result = await self._call(service, mock_db, adapter, target)
        rom = result.summary_cards[0]
        assert rom.nights == 3  # Mar 29, 30, 31
