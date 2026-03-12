import logging
from datetime import date

import httpx

from app.adapters.base import (
    DataSourceAdapter,
    RawActualRecord,
    RawBudgetRecord,
    RawForecastRecord,
)
from app.adapters.mapping import MappingEngine

logger = logging.getLogger(__name__)


class ProfitSwordAdapter(DataSourceAdapter):
    """ProfitSword API integration. Translates responses via MappingEngine."""

    def __init__(self, base_url: str, api_key: str, mapping: MappingEngine):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-API-Key": api_key},
            timeout=60.0,
        )
        self.mapping = mapping

    async def fetch_daily_actuals(
        self, property_codes: list[str], start_date: date, end_date: date
    ) -> list[RawActualRecord]:
        records = []
        for code in property_codes:
            try:
                resp = await self.client.get(
                    "/api/daily-actuals",
                    params={
                        "property_code": code,
                        "start_date": start_date.isoformat(),
                        "end_date": end_date.isoformat(),
                    },
                )
                resp.raise_for_status()
                for item in resp.json().get("data", []):
                    internal_code = self.mapping.translate(item["account_code"])
                    if internal_code:
                        records.append(RawActualRecord(
                            property_code=code,
                            date=date.fromisoformat(item["date"]),
                            account_code=internal_code,
                            value=int(float(item["value"]) * 100),  # Convert dollars to cents
                            per_unit_value=(
                                int(float(item["per_unit_value"]) * 100)
                                if item.get("per_unit_value") else None
                            ),
                        ))
            except httpx.HTTPError as e:
                logger.error(f"ProfitSword fetch_daily_actuals failed for {code}: {e}")
        return records

    async def fetch_budgets(
        self, property_codes: list[str], year: int
    ) -> list[RawBudgetRecord]:
        records = []
        for code in property_codes:
            try:
                resp = await self.client.get(
                    "/api/budgets",
                    params={"property_code": code, "year": year},
                )
                resp.raise_for_status()
                for item in resp.json().get("data", []):
                    internal_code = self.mapping.translate(item["account_code"])
                    if internal_code:
                        records.append(RawBudgetRecord(
                            property_code=code,
                            year=year,
                            month=item["month"],
                            account_code=internal_code,
                            value=int(float(item["value"]) * 100),
                        ))
            except httpx.HTTPError as e:
                logger.error(f"ProfitSword fetch_budgets failed for {code}: {e}")
        return records

    async def fetch_forecasts(
        self, property_codes: list[str], year: int
    ) -> list[RawForecastRecord]:
        records = []
        for code in property_codes:
            try:
                resp = await self.client.get(
                    "/api/forecasts",
                    params={"property_code": code, "year": year},
                )
                resp.raise_for_status()
                for item in resp.json().get("data", []):
                    internal_code = self.mapping.translate(item["account_code"])
                    if internal_code:
                        records.append(RawForecastRecord(
                            property_code=code,
                            year=year,
                            month=item["month"],
                            account_code=internal_code,
                            value=int(float(item["value"]) * 100),
                        ))
            except httpx.HTTPError as e:
                logger.error(f"ProfitSword fetch_forecasts failed for {code}: {e}")
        return records

    async def close(self):
        await self.client.aclose()
