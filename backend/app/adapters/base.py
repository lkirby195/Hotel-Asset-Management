from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date


@dataclass
class RawActualRecord:
    property_code: str
    date: date
    account_code: str
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
