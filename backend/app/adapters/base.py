from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import date


@dataclass
class RawActualRecord:
    property_code: str  # siteTag
    date: date
    account_code: str  # internal line_item code (after mapping)
    value: int  # cents
    per_unit_value: int | None = None


@dataclass
class RawBudgetRecord:
    property_code: str
    year: int
    month: int
    account_code: str
    value: int  # cents


@dataclass
class RawForecastRecord:
    property_code: str
    year: int
    month: int
    account_code: str
    value: int  # cents


@dataclass
class SiteInfo:
    site_tag: str
    site_name: str
    address1: str = ""
    address2: str = ""
    city: str = ""
    state: str = ""
    zip_code: str = ""


@dataclass
class DataSetInfo:
    dataset_id: int
    description: str


class DataSourceAdapter(ABC):
    """Abstract base for data source integrations (ProfitSword, Opera, M3, etc.)."""

    @abstractmethod
    async def fetch_daily_actuals(
        self, property_codes: list[str], start_date: date, end_date: date
    ) -> list[RawActualRecord]:
        ...

    @abstractmethod
    async def fetch_budgets(
        self, property_codes: list[str], year: int
    ) -> list[RawBudgetRecord]:
        ...

    @abstractmethod
    async def fetch_forecasts(
        self, property_codes: list[str], year: int
    ) -> list[RawForecastRecord]:
        ...

    async def fetch_sites(self) -> list[SiteInfo]:
        """Fetch available properties/sites. Optional — not all adapters support this."""
        return []

    async def fetch_datasets(self) -> list[DataSetInfo]:
        """Fetch available datasets. Optional — not all adapters support this."""
        return []
