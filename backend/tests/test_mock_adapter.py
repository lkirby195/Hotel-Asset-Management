"""Tests for the MockAdapter."""

from datetime import date

import pytest

from app.adapters.mock_adapter import MockAdapter


class TestMockAdapter:
    @pytest.fixture
    def adapter(self):
        return MockAdapter(seed=42)

    async def test_fetch_daily_actuals_returns_records(self, adapter):
        records = await adapter.fetch_daily_actuals(
            property_codes=["PROP1"],
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 1),
        )
        assert len(records) > 0
        # Should have one record per mock line item
        assert all(r.property_code == "PROP1" for r in records)
        assert all(r.date == date(2026, 3, 1) for r in records)

    async def test_fetch_daily_actuals_multi_day(self, adapter):
        records = await adapter.fetch_daily_actuals(
            property_codes=["PROP1"],
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 3),
        )
        dates = {r.date for r in records}
        assert date(2026, 3, 1) in dates
        assert date(2026, 3, 2) in dates
        assert date(2026, 3, 3) in dates

    async def test_fetch_daily_actuals_multi_property(self, adapter):
        records = await adapter.fetch_daily_actuals(
            property_codes=["PROP1", "PROP2"],
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 1),
        )
        codes = {r.property_code for r in records}
        assert codes == {"PROP1", "PROP2"}

    async def test_fetch_daily_actuals_deterministic(self, adapter):
        """Same inputs should produce same outputs."""
        r1 = await adapter.fetch_daily_actuals(["PROP1"], date(2026, 3, 1), date(2026, 3, 1))
        adapter2 = MockAdapter(seed=42)
        r2 = await adapter2.fetch_daily_actuals(["PROP1"], date(2026, 3, 1), date(2026, 3, 1))

        assert len(r1) == len(r2)
        for a, b in zip(r1, r2):
            assert a.value == b.value
            assert a.account_code == b.account_code

    async def test_fetch_daily_actuals_values_in_range(self, adapter):
        records = await adapter.fetch_daily_actuals(["PROP1"], date(2026, 3, 1), date(2026, 3, 1))
        for r in records:
            assert r.value > 0  # All values should be positive

    async def test_fetch_budgets_returns_12_months(self, adapter):
        records = await adapter.fetch_budgets(["PROP1"], 2026)
        months = {r.month for r in records}
        assert months == set(range(1, 13))

    async def test_fetch_budgets_multi_property(self, adapter):
        records = await adapter.fetch_budgets(["PROP1", "PROP2"], 2026)
        codes = {r.property_code for r in records}
        assert codes == {"PROP1", "PROP2"}

    async def test_fetch_forecasts_returns_12_months(self, adapter):
        records = await adapter.fetch_forecasts(["PROP1"], 2026)
        months = {r.month for r in records}
        assert months == set(range(1, 13))

    async def test_fetch_forecasts_values_positive(self, adapter):
        records = await adapter.fetch_forecasts(["PROP1"], 2026)
        for r in records:
            assert r.value > 0

    async def test_empty_property_list(self, adapter):
        records = await adapter.fetch_daily_actuals([], date(2026, 3, 1), date(2026, 3, 1))
        assert records == []

    async def test_record_account_codes_are_strings(self, adapter):
        records = await adapter.fetch_daily_actuals(["P1"], date(2026, 3, 1), date(2026, 3, 1))
        for r in records:
            assert isinstance(r.account_code, str)
            assert len(r.account_code) > 0
