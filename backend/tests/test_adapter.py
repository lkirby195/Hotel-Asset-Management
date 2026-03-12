"""Tests for the ProfitSwordAdapter with mocked HTTP responses."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.adapters.base import DataSetInfo, SiteInfo
from app.adapters.mapping import MappingEngine
from app.adapters.profitsword import (
    ProfitSwordAdapter,
    _dollars_to_cents,
    _stat_to_units,
    _strip_site_prefix,
)


# ── Helper conversion tests ──────────────────────────────────────


class TestDollarsToCents:
    def test_int_value(self):
        assert _dollars_to_cents(100) == 10000

    def test_float_value(self):
        assert _dollars_to_cents(99.99) == 9999

    def test_string_value(self):
        assert _dollars_to_cents("150.50") == 15050

    def test_none_value(self):
        assert _dollars_to_cents(None) == 0

    def test_zero(self):
        assert _dollars_to_cents(0) == 0

    def test_negative(self):
        assert _dollars_to_cents(-50.25) == -5025

    def test_rounding(self):
        assert _dollars_to_cents(10.005) == 1001  # rounds up
        assert _dollars_to_cents(10.004) == 1000  # rounds down


class TestStatToUnits:
    def test_normal_value(self):
        assert _stat_to_units(42) == 4200

    def test_fractional_value(self):
        assert _stat_to_units(3.14) == 314

    def test_zero_returns_none(self):
        assert _stat_to_units(0) is None

    def test_none_returns_none(self):
        assert _stat_to_units(None) is None

    def test_negative_value(self):
        assert _stat_to_units(-5) == -500


class TestStripSitePrefix:
    def test_strips_x_prefix(self):
        assert _strip_site_prefix("xHilton Downtown") == "Hilton Downtown"

    def test_no_prefix(self):
        assert _strip_site_prefix("Hilton Downtown") == "Hilton Downtown"

    def test_empty_string(self):
        assert _strip_site_prefix("") == ""

    def test_just_x(self):
        assert _strip_site_prefix("x") == ""


# ── Adapter tests ─────────────────────────────────────────────────


class TestProfitSwordAdapter:
    @pytest.fixture
    def mapping(self):
        return MappingEngine({
            "RF0141": "room_revenue",
            "RF0002": "rooms_sold",
            "TOTGOP": "gross_operating_profit",
        })

    @pytest.fixture
    def adapter(self, mapping):
        return ProfitSwordAdapter(
            base_url="https://test.profitsage.net/PS-Handlers",
            username="testuser",
            password="testpass",
            mapping=mapping,
        )

    def test_base_url_trailing_slash_stripped(self, mapping):
        adapter = ProfitSwordAdapter(
            base_url="https://test.profitsage.net/PS-Handlers/",
            username="u", password="p", mapping=mapping,
        )
        assert adapter.base_url == "https://test.profitsage.net/PS-Handlers"

    def test_date_formatting(self, adapter):
        assert adapter._fmt_date(date(2026, 3, 1)) == "03/01/2026"
        assert adapter._fmt_date(date(2026, 12, 25)) == "12/25/2026"

    def test_as_of_date_formatting(self, adapter):
        assert adapter._fmt_as_of_date(date(2026, 3, 1)) == "2026-03-01"

    def test_parse_date_iso(self, adapter):
        d = adapter._parse_date("2026-02-15T00:00:00")
        assert d == date(2026, 2, 15)

    def test_parse_date_with_z(self, adapter):
        d = adapter._parse_date("2026-02-15T00:00:00Z")
        assert d == date(2026, 2, 15)

    def test_parse_date_mm_dd_yyyy(self, adapter):
        d = adapter._parse_date("02/15/2026")
        assert d == date(2026, 2, 15)

    def test_parse_date_empty(self, adapter):
        assert adapter._parse_date("") is None
        assert adapter._parse_date(None) is None

    def test_parse_date_invalid(self, adapter):
        assert adapter._parse_date("not-a-date") is None

    async def test_ensure_token_caches(self, adapter):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"access_token": "tok123", "expires_in": 3600}
        adapter.client.post = AsyncMock(return_value=mock_response)

        token1 = await adapter._ensure_token()
        token2 = await adapter._ensure_token()

        assert token1 == "tok123"
        assert token2 == "tok123"
        # Should only make one HTTP call (cached)
        assert adapter.client.post.call_count == 1

    async def test_ensure_token_refreshes_when_expired(self, adapter):
        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"access_token": "tok456", "expires_in": 3600}
        adapter.client.post = AsyncMock(return_value=mock_response)

        # Force token expiry
        adapter._token = "old_token"
        adapter._token_expires_at = 0

        token = await adapter._ensure_token()
        assert token == "tok456"
        assert adapter.client.post.call_count == 1

    async def test_get_handles_no_data_string(self, adapter):
        """API returns 'No data downloaded.' as a JSON string."""
        adapter._ensure_token = AsyncMock(return_value="tok")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = "No data downloaded."

        adapter._request_with_retry = AsyncMock(return_value=mock_resp)

        result = await adapter._get("DailyExtended", {"siteTag": "PROP1"})
        assert result == []

    async def test_get_handles_list_response(self, adapter):
        adapter._ensure_token = AsyncMock(return_value="tok")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.return_value = [{"itemTag": "RF0141", "amt": 100}]

        adapter._request_with_retry = AsyncMock(return_value=mock_resp)

        result = await adapter._get("DailyExtended", {})
        assert len(result) == 1
        assert result[0]["itemTag"] == "RF0141"

    async def test_get_handles_non_json(self, adapter):
        adapter._ensure_token = AsyncMock(return_value="tok")

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json.side_effect = Exception("Bad JSON")
        mock_resp.text = "Internal Server Error"

        adapter._request_with_retry = AsyncMock(return_value=mock_resp)

        result = await adapter._get("DailyExtended", {})
        assert result == []

    async def test_fetch_daily_actuals_maps_codes(self, adapter):
        """Tests that fetch_daily_actuals correctly maps itemTags to internal codes."""
        adapter._fetch_daily_extended = AsyncMock(return_value=[
            {"itemTag": "RF0141", "amt": 50000.0, "stat": 0, "date": "2026-03-01T00:00:00"},
            {"itemTag": "RF0002", "amt": 0, "stat": 150, "date": "2026-03-01T00:00:00"},
            {"itemTag": "UNMAPPED_TAG", "amt": 100, "stat": 0, "date": "2026-03-01T00:00:00"},
        ])

        records = await adapter.fetch_daily_actuals(
            property_codes=["PROP1"],
            start_date=date(2026, 3, 1),
            end_date=date(2026, 3, 1),
        )

        # UNMAPPED_TAG should be skipped
        assert len(records) == 2
        codes = {r.account_code for r in records}
        assert "room_revenue" in codes
        assert "rooms_sold" in codes

    async def test_fetch_daily_actuals_converts_cents(self, adapter):
        adapter._fetch_daily_extended = AsyncMock(return_value=[
            {"itemTag": "RF0141", "amt": 500.50, "stat": 0, "date": "2026-03-01T00:00:00"},
        ])

        records = await adapter.fetch_daily_actuals(["PROP1"], date(2026, 3, 1), date(2026, 3, 1))
        assert records[0].value == 50050  # $500.50 = 50050 cents

    async def test_fetch_daily_actuals_handles_http_error(self, adapter):
        adapter._fetch_daily_extended = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))

        records = await adapter.fetch_daily_actuals(["PROP1"], date(2026, 3, 1), date(2026, 3, 1))
        assert records == []

    async def test_fetch_budgets_calls_per_month(self, adapter):
        adapter._fetch_daily_extended = AsyncMock(return_value=[
            {"itemTag": "RF0141", "amt": 100000, "stat": 0, "date": ""},
        ])

        records = await adapter.fetch_budgets_monthly(["PROP1"], 2026)
        # Should call 12 times (once per month)
        assert adapter._fetch_daily_extended.call_count == 12
        assert len(records) == 12  # 1 mapped tag * 12 months

    async def test_fetch_forecasts_uses_as_of_date(self, adapter):
        adapter._fetch_daily_extended = AsyncMock(return_value=[
            {"itemTag": "RF0141", "amt": 100000, "stat": 0, "date": ""},
        ])

        await adapter.fetch_forecasts(["PROP1"], 2026)

        # Check January call uses Dec 31 prior year as asOfDate
        jan_call = adapter._fetch_daily_extended.call_args_list[0]
        assert jan_call.kwargs.get("as_of_date") == date(2025, 12, 31)

        # Check March call uses Feb 28 as asOfDate
        mar_call = adapter._fetch_daily_extended.call_args_list[2]
        assert mar_call.kwargs.get("as_of_date") == date(2026, 2, 28)

    async def test_fetch_sites_excludes_tmp(self, adapter):
        adapter._get = AsyncMock(return_value=[
            {"siteTag": "PROP1", "siteName": "Hotel One", "siteAddress1": "", "siteAddress2": "", "siteCity": "NYC", "siteState": "NY", "siteZip": "10001"},
            {"siteTag": "TMP1", "siteName": "Temp 1", "siteAddress1": "", "siteAddress2": "", "siteCity": "", "siteState": "", "siteZip": ""},
            {"siteTag": "TMP2", "siteName": "Temp 2", "siteAddress1": "", "siteAddress2": "", "siteCity": "", "siteState": "", "siteZip": ""},
        ])

        sites = await adapter.fetch_sites()
        assert len(sites) == 1
        assert sites[0].site_tag == "PROP1"

    async def test_fetch_sites_strips_x_prefix(self, adapter):
        adapter._get = AsyncMock(return_value=[
            {"siteTag": "PROP1", "siteName": "xOld Hotel", "siteAddress1": "", "siteAddress2": "", "siteCity": "", "siteState": "", "siteZip": ""},
        ])

        sites = await adapter.fetch_sites()
        assert sites[0].site_name == "Old Hotel"

    async def test_fetch_datasets(self, adapter):
        adapter._get = AsyncMock(return_value=[
            {"fcid": -3, "description": "Actuals"},
            {"fcid": 2, "description": "Budget"},
        ])

        datasets = await adapter.fetch_datasets()
        assert len(datasets) == 2
        assert datasets[0].dataset_id == -3
        assert datasets[0].description == "Actuals"

    async def test_close(self, adapter):
        adapter.client.aclose = AsyncMock()
        await adapter.close()
        adapter.client.aclose.assert_called_once()
