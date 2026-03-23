"""Mock adapter for local development without ProfitSword API access."""

import random
from datetime import date, timedelta

from app.adapters.base import (
    DataSourceAdapter,
    RawActualRecord,
    RawBudgetRecord,
    RawForecastRecord,
    RawOTBRecord,
)

# Internal line item codes that the mock generates data for
MOCK_LINE_ITEMS = [
    ("room_revenue", 50000_00, 80000_00),       # $500-$800/day
    ("other_room_revenue", 2000_00, 5000_00),
    ("food_revenue", 15000_00, 30000_00),
    ("beverage_revenue", 5000_00, 12000_00),
    ("catering_revenue", 3000_00, 20000_00),
    ("spa_services_revenue", 2000_00, 8000_00),
    ("spa_retail_revenue", 500_00, 2000_00),
    ("golf_greens_revenue", 3000_00, 10000_00),
    ("golf_cart_revenue", 1000_00, 4000_00),
    ("golf_pro_shop_revenue", 500_00, 3000_00),
    ("parking_revenue", 1000_00, 3000_00),
    ("telecom_revenue", 200_00, 800_00),
    ("misc_revenue", 500_00, 2000_00),
    ("rooms_labor", 12000_00, 20000_00),
    ("rooms_ota_commissions", 3000_00, 8000_00),
    ("rooms_supplies", 1000_00, 3000_00),
    ("rooms_other_expense", 500_00, 2000_00),
    ("fb_cost_of_sales", 5000_00, 10000_00),
    ("fb_labor", 8000_00, 15000_00),
    ("fb_other_expense", 1000_00, 3000_00),
    ("spa_labor", 2000_00, 5000_00),
    ("spa_cost_of_sales", 500_00, 2000_00),
    ("spa_other_expense", 300_00, 1000_00),
    ("golf_labor", 2000_00, 6000_00),
    ("golf_maintenance", 1000_00, 4000_00),
    ("golf_other_expense", 300_00, 1500_00),
    ("ag_salaries", 5000_00, 8000_00),
    ("ag_professional_fees", 500_00, 3000_00),
    ("ag_other", 500_00, 2000_00),
    ("sm_salaries", 3000_00, 6000_00),
    ("sm_advertising", 1000_00, 5000_00),
    ("sm_other", 500_00, 2000_00),
    ("pom_salaries", 2000_00, 5000_00),
    ("pom_repairs", 1000_00, 4000_00),
    ("pom_utilities", 2000_00, 6000_00),
    ("energy_electric", 3000_00, 8000_00),
    ("energy_gas", 1000_00, 4000_00),
    ("energy_water", 800_00, 2500_00),
    ("management_fee", 4000_00, 7000_00),
    ("property_tax", 3000_00, 3500_00),
    ("insurance", 1500_00, 2000_00),
    ("rent_lease", 5000_00, 5500_00),
]


class MockAdapter(DataSourceAdapter):
    """Generates deterministic mock data for development."""

    def __init__(self, seed: int = 42):
        self._rng = random.Random(seed)

    async def fetch_daily_actuals(
        self, property_codes: list[str], start_date: date, end_date: date
    ) -> list[RawActualRecord]:
        records = []
        current = start_date
        while current <= end_date:
            for code in property_codes:
                # Use property code + date as seed for consistency
                day_seed = hash(f"{code}:{current.isoformat()}")
                rng = random.Random(day_seed)
                for item_code, low, high in MOCK_LINE_ITEMS:
                    value = rng.randint(low, high)
                    records.append(RawActualRecord(
                        property_code=code,
                        date=current,
                        account_code=item_code,
                        value=value,
                    ))
            current += timedelta(days=1)
        return records

    async def fetch_budgets(
        self, property_codes: list[str], year: int
    ) -> list[RawBudgetRecord]:
        records = []
        for code in property_codes:
            for month in range(1, 13):
                month_seed = hash(f"{code}:budget:{year}:{month}")
                rng = random.Random(month_seed)
                for item_code, low, high in MOCK_LINE_ITEMS:
                    # Budget = ~30 days * average daily value
                    avg_daily = (low + high) // 2
                    monthly = avg_daily * 30
                    # Add some variance
                    monthly = int(monthly * rng.uniform(0.9, 1.1))
                    records.append(RawBudgetRecord(
                        property_code=code,
                        year=year,
                        month=month,
                        account_code=item_code,
                        value=monthly,
                    ))
        return records

    async def fetch_otb(
        self, property_codes: list[str], start_date: date, end_date: date
    ) -> list[RawOTBRecord]:
        """Generate deterministic mock OTB data for forward-looking dates."""
        records = []
        current = start_date
        while current <= end_date:
            for code in property_codes:
                day_seed = hash(f"{code}:otb:{current.isoformat()}")
                rng = random.Random(day_seed)
                rooms = rng.randint(80, 150)
                revenue = rng.randint(40000_00, 70000_00)
                adr = revenue // rooms if rooms else 0
                records.append(RawOTBRecord(
                    property_code=code,
                    date=current,
                    rooms=rooms,
                    revenue=revenue,
                    adr=adr,
                ))
            current += timedelta(days=1)
        return records

    async def fetch_forecasts(
        self, property_codes: list[str], year: int
    ) -> list[RawForecastRecord]:
        records = []
        for code in property_codes:
            for month in range(1, 13):
                month_seed = hash(f"{code}:forecast:{year}:{month}")
                rng = random.Random(month_seed)
                for item_code, low, high in MOCK_LINE_ITEMS:
                    avg_daily = (low + high) // 2
                    monthly = avg_daily * 30
                    monthly = int(monthly * rng.uniform(0.85, 1.15))
                    records.append(RawForecastRecord(
                        property_code=code,
                        year=year,
                        month=month,
                        account_code=item_code,
                        value=monthly,
                    ))
        return records
