"""ProfitSword / ProfitSage Data Portal v3 adapter.

Key learnings from working daily_report codebase:
- Auth: POST {base}/token with grant_type=password (token as query param, not header)
- All financial data comes via GET DailyExtended (not MonthlyExtended)
- includeTotals must be "Y" (not "true"/"false") — API returns nothing without it
- BD/ED use MM/dd/yyyy format; asOfDate uses YYYY-MM-DD
- Response fields: siteTag, siteName, itemTag, description, accountNumber, statAccount, date, asOfDate, stat, amt
- Each row has dual values: amt (dollars) and stat (units/rooms/hours)
- Date ranges return pre-aggregated sums per itemTag per site
- Dataset IDs: Actuals=-3, Budget=2, Forecast=1, OTB=-5
"""

import logging
import time
from datetime import date, datetime

import httpx

from app.adapters.base import (
    DataSetInfo,
    DataSourceAdapter,
    RawActualRecord,
    RawBudgetRecord,
    RawForecastRecord,
    RawOTBRecord,
    SiteInfo,
)
from app.adapters.mapping import MappingEngine

logger = logging.getLogger(__name__)

# ProfitSage dataset IDs
DATASET_ACTUALS = -3
DATASET_BUDGET = 2
DATASET_FORECAST = 1
DATASET_OTB = -5

# Revenue account codes for OTB aggregation. Only these tags contribute to
# the revenue total; other mapped tags (occupancy stats, KPIs, labor/expense
# codes) are ignored to avoid inflating revenue.
_OTB_REVENUE_CODES = {
    "room_revenue",
    "transient_revenue",
    "group_revenue",
    "other_room_revenue",
}


class ProfitSwordAdapter(DataSourceAdapter):
    """ProfitSword / ProfitSage Data Portal v3 integration."""

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        mapping: MappingEngine,
        dataset_actuals: int = DATASET_ACTUALS,
        dataset_budget: int = DATASET_BUDGET,
        dataset_forecast: int = DATASET_FORECAST,
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
        """Make an authenticated GET to Data Portal v3. Returns list of dicts or []."""
        token = await self._ensure_token()
        params["access_token"] = token
        url = f"{self.base_url}/api/DataPortalv3/{endpoint}"

        resp = await self._request_with_retry(url, params)
        resp.raise_for_status()

        # API returns a JSON string "No data downloaded." when empty
        try:
            data = resp.json()
        except Exception:
            logger.warning(f"{endpoint}: non-JSON response ({resp.text[:100]})")
            return []

        if isinstance(data, str):
            if "no data" in data.lower():
                logger.debug(f"{endpoint}: no data for params {params}")
            else:
                logger.warning(f"{endpoint}: unexpected string response: {data[:100]}")
            return []

        if not isinstance(data, list):
            logger.warning(f"{endpoint}: unexpected response type {type(data)}")
            return []

        return data

    async def _request_with_retry(
        self, url: str, params: dict, max_retries: int = 2
    ) -> httpx.Response:
        """GET with retry on 429/5xx and connection errors."""
        last_exc = None
        for attempt in range(max_retries + 1):
            try:
                resp = await self.client.get(url, params=params)
                if resp.status_code in (429, 500, 502, 503, 504) and attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                return resp
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                last_exc = e
                if attempt < max_retries:
                    import asyncio
                    await asyncio.sleep(1 * (attempt + 1))
                    continue
                raise
        raise last_exc  # type: ignore

    # ── Date formatting ────────────────────────────────────────────

    @staticmethod
    def _fmt_date(d: date) -> str:
        """Format date as MM/dd/yyyy for BD/ED params."""
        return d.strftime("%m/%d/%Y")

    @staticmethod
    def _fmt_as_of_date(d: date) -> str:
        """Format date as YYYY-MM-DD for asOfDate param."""
        return d.strftime("%Y-%m-%d")

    # ── Core: DailyExtended ────────────────────────────────────────

    async def _fetch_daily_extended(
        self,
        site_tag: str,
        start_date: date,
        end_date: date,
        dataset_id: int,
        as_of_date: date | None = None,
    ) -> list[dict]:
        """Call DailyExtended for a single site. Returns raw row dicts."""
        params = {
            "dataSetID": dataset_id,
            "BD": self._fmt_date(start_date),
            "ED": self._fmt_date(end_date),
            "siteTag": site_tag,
            "includeTotals": "Y",
            "includeZeroes": "N",
        }
        if as_of_date:
            params["asOfDate"] = self._fmt_as_of_date(as_of_date)

        return await self._get("DailyExtended", params)

    # ── Public API: fetch_daily_actuals ────────────────────────────

    async def fetch_daily_actuals(
        self, property_codes: list[str], start_date: date, end_date: date
    ) -> list[RawActualRecord]:
        """Fetch daily actuals via DailyExtended (dataSetID=-3).

        When a date range is provided, the API returns pre-aggregated
        sums per itemTag per site (one row per tag, not per day).
        """
        records: list[RawActualRecord] = []

        for site_tag in property_codes:
            try:
                data = await self._fetch_daily_extended(
                    site_tag, start_date, end_date, self.dataset_actuals
                )
                for row in data:
                    item_tag = str(row.get("itemTag", ""))
                    internal_code = self.mapping.translate(item_tag)
                    if not internal_code:
                        continue

                    row_date = self._parse_date(row.get("date", ""))
                    if not row_date:
                        # For aggregated ranges, date may be the end date
                        row_date = end_date

                    records.append(RawActualRecord(
                        property_code=site_tag,
                        date=row_date,
                        account_code=internal_code,
                        value=_dollars_to_cents(row.get("amt")),
                        per_unit_value=_stat_to_units(row.get("stat")),
                    ))

            except httpx.HTTPError as e:
                logger.error(f"DailyExtended actuals failed for {site_tag}: {e}")

        logger.info(f"Fetched {len(records)} daily actual records from {len(property_codes)} sites")
        return records

    # ── Public API: fetch_budgets ──────────────────────────────────

    async def fetch_budgets(
        self, property_codes: list[str], year: int
    ) -> list[RawBudgetRecord]:
        """Fetch budget data via DailyExtended (dataSetID=2).

        Fetches full year as a single range. The API returns one row per
        itemTag per site with the sum for the entire date range.
        """
        start = date(year, 1, 1)
        end = date(year, 12, 31)
        records: list[RawBudgetRecord] = []

        for site_tag in property_codes:
            try:
                data = await self._fetch_daily_extended(
                    site_tag, start, end, self.dataset_budget
                )
                for row in data:
                    item_tag = str(row.get("itemTag", ""))
                    internal_code = self.mapping.translate(item_tag)
                    if not internal_code:
                        continue

                    # Budget from DailyExtended is aggregated for the full range.
                    # We store as year/month=0 to indicate annual, or fetch per-month
                    # if needed. For now, store annual totals.
                    records.append(RawBudgetRecord(
                        property_code=site_tag,
                        year=year,
                        month=0,  # annual total
                        account_code=internal_code,
                        value=_dollars_to_cents(row.get("amt")),
                    ))

            except httpx.HTTPError as e:
                logger.error(f"DailyExtended budget failed for {site_tag}: {e}")

        logger.info(f"Fetched {len(records)} budget records")
        return records

    async def fetch_budgets_monthly(
        self, property_codes: list[str], year: int
    ) -> list[RawBudgetRecord]:
        """Fetch budget data month-by-month for proper proration.

        Makes 12 API calls per site (one per month) to get monthly totals.
        """
        records: list[RawBudgetRecord] = []
        import calendar

        for site_tag in property_codes:
            for month in range(1, 13):
                try:
                    start = date(year, month, 1)
                    last_day = calendar.monthrange(year, month)[1]
                    end = date(year, month, last_day)

                    data = await self._fetch_daily_extended(
                        site_tag, start, end, self.dataset_budget
                    )
                    for row in data:
                        item_tag = str(row.get("itemTag", ""))
                        internal_code = self.mapping.translate(item_tag)
                        if not internal_code:
                            continue

                        records.append(RawBudgetRecord(
                            property_code=site_tag,
                            year=year,
                            month=month,
                            account_code=internal_code,
                            value=_dollars_to_cents(row.get("amt")),
                        ))

                except httpx.HTTPError as e:
                    logger.error(f"Budget month {month} failed for {site_tag}: {e}")

        logger.info(f"Fetched {len(records)} monthly budget records")
        return records

    # ── Public API: fetch_forecasts ────────────────────────────────

    async def fetch_forecasts(
        self, property_codes: list[str], year: int
    ) -> list[RawForecastRecord]:
        """Fetch forecast data via DailyExtended (dataSetID=1).

        Uses asOfDate = end of prior month for the current forecast snapshot.
        """
        records: list[RawForecastRecord] = []
        import calendar

        for site_tag in property_codes:
            for month in range(1, 13):
                try:
                    start = date(year, month, 1)
                    last_day = calendar.monthrange(year, month)[1]
                    end = date(year, month, last_day)

                    # asOfDate = end of prior month (forecast as of that snapshot)
                    if month == 1:
                        as_of = date(year - 1, 12, 31)
                    else:
                        prev_last_day = calendar.monthrange(year, month - 1)[1]
                        as_of = date(year, month - 1, prev_last_day)

                    data = await self._fetch_daily_extended(
                        site_tag, start, end, self.dataset_forecast, as_of_date=as_of
                    )
                    for row in data:
                        item_tag = str(row.get("itemTag", ""))
                        internal_code = self.mapping.translate(item_tag)
                        if not internal_code:
                            continue

                        records.append(RawForecastRecord(
                            property_code=site_tag,
                            year=year,
                            month=month,
                            account_code=internal_code,
                            value=_dollars_to_cents(row.get("amt")),
                        ))

                except httpx.HTTPError as e:
                    logger.error(f"Forecast month {month} failed for {site_tag}: {e}")

        logger.info(f"Fetched {len(records)} forecast records")
        return records

    # ── Public API: fetch_otb ────────────────────────────────────

    async def fetch_otb(
        self, property_codes: list[str], start_date: date, end_date: date
    ) -> list[RawOTBRecord]:
        """Fetch on-the-books data via DailyExtended (dataSetID=-5).

        Same pattern as fetch_daily_actuals but returns RawOTBRecord
        with rooms from stat field and revenue from amt field.
        """
        records: list[RawOTBRecord] = []

        for site_tag in property_codes:
            try:
                data = await self._fetch_daily_extended(
                    site_tag, start_date, end_date, DATASET_OTB
                )

                # Aggregate all itemTags into one record per site per date.
                # Key: (site_tag, date) -> {rooms, revenue}
                agg: dict[tuple[str, date], dict] = {}
                for row in data:
                    item_tag = str(row.get("itemTag", ""))
                    internal_code = self.mapping.translate(item_tag)
                    if not internal_code:
                        continue

                    row_date = self._parse_date(row.get("date", ""))
                    if not row_date:
                        row_date = end_date

                    key = (site_tag, row_date)
                    if key not in agg:
                        agg[key] = {"rooms": 0, "revenue": 0}

                    # Only sum revenue from tags that represent actual revenue.
                    # The mapping config includes non-revenue tags (available_rooms,
                    # occupied_rooms, adr, revpar, labor codes, expense codes, etc.)
                    # that would incorrectly inflate the revenue total if included.
                    if internal_code == "rooms_sold":
                        agg[key]["rooms"] += int(round(float(row.get("stat", 0))))
                    elif internal_code in _OTB_REVENUE_CODES:
                        agg[key]["revenue"] += _dollars_to_cents(row.get("amt"))

                for (st, dt), vals in agg.items():
                    rooms = vals["rooms"]
                    revenue = vals["revenue"]
                    adr = revenue // rooms if rooms else 0
                    records.append(RawOTBRecord(
                        property_code=st,
                        date=dt,
                        rooms=rooms,
                        revenue=revenue,
                        adr=adr,
                    ))

            except httpx.HTTPError as e:
                logger.error(f"DailyExtended OTB failed for {site_tag}: {e}")

        logger.info(f"Fetched {len(records)} OTB records from {len(property_codes)} sites")
        return records

    # ── Discovery endpoints ────────────────────────────────────────

    async def fetch_sites(self) -> list[SiteInfo]:
        """Fetch all available properties/sites."""
        data = await self._get("Sites", {})
        return [
            SiteInfo(
                site_tag=row.get("siteTag", ""),
                site_name=_strip_site_prefix(row.get("siteName", "")),
                address1=row.get("siteAddress1", ""),
                address2=row.get("siteAddress2", ""),
                city=row.get("siteCity", ""),
                state=row.get("siteState", ""),
                zip_code=row.get("siteZip", ""),
            )
            for row in data
            if row.get("siteTag") not in ("TMP1", "TMP2")
        ]

    async def fetch_datasets(self) -> list[DataSetInfo]:
        """Fetch all available dataset IDs and descriptions."""
        data = await self._get("DataSets", {})
        return [
            DataSetInfo(
                dataset_id=row.get("fcid", 0),
                description=row.get("description", ""),
            )
            for row in data
        ]

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _parse_date(value: str) -> date | None:
        """Parse date from ProfitSword response.

        API returns dates as ISO format: '2026-02-15T00:00:00'
        """
        if not value:
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
        except (ValueError, TypeError):
            pass
        # Fallback: try MM/dd/yyyy
        try:
            return datetime.strptime(value, "%m/%d/%Y").date()
        except (ValueError, TypeError):
            pass
        logger.warning(f"Unparseable date: {value}")
        return None

    async def close(self):
        await self.client.aclose()


def _dollars_to_cents(value) -> int:
    """Convert a dollar amount (float/int/str) to integer cents."""
    if value is None:
        return 0
    return int(round(float(value) * 100))


def _stat_to_units(value) -> int | None:
    """Convert a stat value to integer units (rooms, hours, etc.).

    Returns None if stat is 0 or missing (most stat fields are unused).
    """
    if value is None:
        return None
    val = float(value)
    if val == 0:
        return None
    # Store as integer (multiply by 100 for fractional precision)
    return int(round(val * 100))


def _strip_site_prefix(name: str) -> str:
    """Strip 'x' prefix from site names (indicates inactive/legacy)."""
    if name and name.startswith("x"):
        return name[1:]
    return name
