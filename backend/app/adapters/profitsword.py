import logging
import time
from datetime import date

import httpx

from app.adapters.base import (
    DataSetInfo,
    DataSourceAdapter,
    RawActualRecord,
    RawBudgetRecord,
    RawForecastRecord,
    SiteInfo,
)
from app.adapters.mapping import MappingEngine

logger = logging.getLogger(__name__)


class ProfitSwordAdapter(DataSourceAdapter):
    """ProfitSword / ProfitSage Data Portal v3 integration.

    Auth: OAuth-style token (username + password → bearer token).
    Endpoints: DailyExtended (daily actuals), MonthlyExtended (monthly actuals/budgets/forecasts).
    """

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        mapping: MappingEngine,
        dataset_actuals: int,
        dataset_budget: int,
        dataset_forecast: int,
    ):
        self.base_url = base_url.rstrip("/")
        self._username = username
        self._password = password
        self.mapping = mapping
        self.dataset_actuals = dataset_actuals
        self.dataset_budget = dataset_budget
        self.dataset_forecast = dataset_forecast

        self._token: str | None = None
        self._token_expires_at: float = 0

        self.client = httpx.AsyncClient(timeout=120.0)

    # ── Token management ───────────────────────────────────────────

    async def _ensure_token(self) -> str:
        """Get a valid bearer token, refreshing if expired."""
        if self._token and time.time() < self._token_expires_at:
            return self._token

        resp = await self.client.post(
            f"{self.base_url}/token",
            data={
                "grant_type": "password",
                "username": self._username,
                "password": self._password,
            },
            headers={
                "Accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
            },
        )
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        # Expire 60s early to avoid edge cases
        self._token_expires_at = time.time() + data.get("expires_in", 3599) - 60
        logger.info("ProfitSword token refreshed")
        return self._token

    async def _get(self, endpoint: str, params: dict) -> list[dict]:
        """Make an authenticated GET request to the Data Portal v3 API."""
        token = await self._ensure_token()
        params["access_token"] = token
        url = f"{self.base_url}/api/DataPortalv3/{endpoint}"

        resp = await self.client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

    # ── Date formatting ────────────────────────────────────────────

    @staticmethod
    def _fmt_date(d: date) -> str:
        """Format date as MM/dd/yyyy (ProfitSword convention)."""
        return d.strftime("%m/%d/%Y")

    # ── Core data fetching ─────────────────────────────────────────

    async def fetch_daily_actuals(
        self, property_codes: list[str], start_date: date, end_date: date
    ) -> list[RawActualRecord]:
        """Fetch daily actuals via DailyExtended endpoint."""
        records: list[RawActualRecord] = []

        for site_tag in property_codes:
            try:
                data = await self._get("DailyExtended", {
                    "dataSetID": self.dataset_actuals,
                    "bd": self._fmt_date(start_date),
                    "ed": self._fmt_date(end_date),
                    "siteTag": site_tag,
                    "includeTotals": "false",
                    "includeZeroes": "false",
                })

                for row in data:
                    item_tag = str(row.get("itemTag", ""))
                    internal_code = self.mapping.translate(item_tag)
                    if not internal_code:
                        continue

                    row_date = self._parse_date(row.get("date", ""))
                    if not row_date:
                        continue

                    amt = row.get("amt", 0)
                    qty = row.get("qty")

                    records.append(RawActualRecord(
                        property_code=site_tag,
                        date=row_date,
                        account_code=internal_code,
                        value=_dollars_to_cents(amt),
                        per_unit_value=_dollars_to_cents(qty) if qty else None,
                    ))

            except httpx.HTTPError as e:
                logger.error(f"DailyExtended failed for {site_tag}: {e}")

        logger.info(f"Fetched {len(records)} daily actual records")
        return records

    async def fetch_budgets(
        self, property_codes: list[str], year: int
    ) -> list[RawBudgetRecord]:
        """Fetch budget data via MonthlyExtended endpoint."""
        return await self._fetch_monthly(
            property_codes, year, self.dataset_budget, "budget"
        )

    async def fetch_forecasts(
        self, property_codes: list[str], year: int
    ) -> list[RawForecastRecord]:
        """Fetch forecast data via MonthlyExtended endpoint."""
        return await self._fetch_monthly(
            property_codes, year, self.dataset_forecast, "forecast"
        )

    async def _fetch_monthly(
        self,
        property_codes: list[str],
        year: int,
        dataset_id: int,
        label: str,
    ) -> list[RawBudgetRecord] | list[RawForecastRecord]:
        """Shared logic for MonthlyExtended (budgets and forecasts use same endpoint)."""
        RecordClass = RawBudgetRecord if label == "budget" else RawForecastRecord
        records = []

        for site_tag in property_codes:
            try:
                data = await self._get("MonthlyExtended", {
                    "dataSetID": dataset_id,
                    "year": year,
                    "begmonth": 1,
                    "endmonth": 12,
                    "siteTag": site_tag,
                    "includeTotals": "false",
                    "includeZeroes": "false",
                })

                for row in data:
                    item_tag = str(row.get("itemTag", ""))
                    internal_code = self.mapping.translate(item_tag)
                    if not internal_code:
                        continue

                    month = row.get("month") or row.get("fiscalPeriod")
                    if not month:
                        continue

                    amt = row.get("amt", 0)
                    records.append(RecordClass(
                        property_code=site_tag,
                        year=year,
                        month=int(month),
                        account_code=internal_code,
                        value=_dollars_to_cents(amt),
                    ))

            except httpx.HTTPError as e:
                logger.error(f"MonthlyExtended ({label}) failed for {site_tag}: {e}")

        logger.info(f"Fetched {len(records)} {label} records")
        return records

    # ── Discovery endpoints ────────────────────────────────────────

    async def fetch_sites(self) -> list[SiteInfo]:
        """Fetch all available properties/sites."""
        data = await self._get("Sites", {})
        return [
            SiteInfo(
                site_tag=row.get("siteTag", ""),
                site_name=row.get("siteName", ""),
                address1=row.get("siteAddress1", ""),
                address2=row.get("siteAddress2", ""),
                city=row.get("siteCity", ""),
                state=row.get("siteState", ""),
                zip_code=row.get("siteZip", ""),
            )
            for row in data
        ]

    async def fetch_datasets(self) -> list[DataSetInfo]:
        """Fetch all available dataset IDs and descriptions."""
        data = await self._get("DataSets", {})
        return [
            DataSetInfo(
                dataset_id=row.get("dataSetID", 0),
                description=row.get("description", ""),
            )
            for row in data
        ]

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _parse_date(value: str) -> date | None:
        """Parse date from ProfitSword response (multiple formats)."""
        if not value:
            return None
        for fmt in ("%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
            try:
                from datetime import datetime
                return datetime.strptime(value.split("T")[0] if "T" in value else value, fmt.split("T")[0]).date()
            except ValueError:
                continue
        logger.warning(f"Unparseable date: {value}")
        return None

    async def close(self):
        await self.client.aclose()


def _dollars_to_cents(value) -> int:
    """Convert a dollar amount (float/int/str) to integer cents."""
    if value is None:
        return 0
    return int(round(float(value) * 100))
