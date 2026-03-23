import calendar
import uuid
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.dashboard import YesterdayKPI, YesterdayResponse


# Line item codes for the KPIs we need
_REVENUE_CODE = "room_revenue"
_ROOMS_SOLD_CODE = "rooms_sold"
_AVAILABLE_ROOMS_CODE = "available_rooms"
_LABOR_PATTERN = "%_labor"


class DashboardService:

    async def get_yesterday(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        property_name: str,
        target_date: date | None = None,
    ) -> YesterdayResponse:
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        actuals = await self._fetch_day_actuals(db, property_id, target_date)
        stly_date = self._same_day_last_year(target_date)
        stly_actuals = await self._fetch_day_actuals(db, property_id, stly_date)
        budget_vals = await self._fetch_prorated_budget(db, property_id, target_date)

        room_revenue = actuals.get(_REVENUE_CODE, 0)
        rooms_sold = actuals.get(_ROOMS_SOLD_CODE, 0)
        available_rooms = actuals.get(_AVAILABLE_ROOMS_CODE, 0)
        total_labor = self._sum_labor(actuals)

        occupancy = (rooms_sold / available_rooms) if available_rooms else 0.0
        adr = (room_revenue / rooms_sold) if rooms_sold else 0.0
        revpar = (room_revenue / available_rooms) if available_rooms else 0.0

        stly_room_revenue = stly_actuals.get(_REVENUE_CODE, 0)
        stly_rooms_sold = stly_actuals.get(_ROOMS_SOLD_CODE, 0)
        stly_available = stly_actuals.get(_AVAILABLE_ROOMS_CODE, 0)
        stly_labor = self._sum_labor(stly_actuals)
        stly_occupancy = (stly_rooms_sold / stly_available) if stly_available else 0.0
        stly_adr = (stly_room_revenue / stly_rooms_sold) if stly_rooms_sold else 0.0
        stly_revpar = (stly_room_revenue / stly_available) if stly_available else 0.0

        budget_room_rev = budget_vals.get(_REVENUE_CODE, 0)
        budget_rooms_sold = budget_vals.get(_ROOMS_SOLD_CODE, 0)
        budget_available = budget_vals.get(_AVAILABLE_ROOMS_CODE, 0)
        budget_labor = self._sum_labor(budget_vals)
        budget_occupancy = (budget_rooms_sold / budget_available) if budget_available else 0.0
        budget_adr = (budget_room_rev / budget_rooms_sold) if budget_rooms_sold else 0.0
        budget_revpar = (budget_room_rev / budget_available) if budget_available else 0.0

        kpis = [
            self._make_kpi("Rooms Sold", rooms_sold, budget_rooms_sold, stly_rooms_sold, "integer"),
            self._make_kpi("Occupancy", occupancy, budget_occupancy, stly_occupancy, "percentage"),
            self._make_kpi("ADR", adr, budget_adr, stly_adr, "currency"),
            self._make_kpi("RevPAR", revpar, budget_revpar, stly_revpar, "currency"),
            self._make_kpi("Room Revenue", room_revenue, budget_room_rev, stly_room_revenue, "currency"),
            self._make_kpi("Total Labor", total_labor, budget_labor, stly_labor, "currency"),
        ]

        return YesterdayResponse(
            property_id=property_id,
            property_name=property_name,
            date=target_date,
            kpis=kpis,
        )

    # ── helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _make_kpi(
        name: str,
        actual: float,
        budget: float,
        stly: float,
        unit: str,
    ) -> YesterdayKPI:
        var_budget = actual - budget
        var_stly = actual - stly
        var_budget_pct = (var_budget / budget * 100) if budget else None
        var_stly_pct = (var_stly / stly * 100) if stly else None
        return YesterdayKPI(
            metric_name=name,
            actual=actual,
            budget=budget,
            stly=stly,
            variance_budget=var_budget,
            variance_budget_pct=round(var_budget_pct, 1) if var_budget_pct is not None else None,
            variance_stly=var_stly,
            variance_stly_pct=round(var_stly_pct, 1) if var_stly_pct is not None else None,
            unit=unit,
        )

    @staticmethod
    def _same_day_last_year(d: date) -> date:
        try:
            return d.replace(year=d.year - 1)
        except ValueError:
            # Feb 29 → Feb 28
            return d.replace(year=d.year - 1, day=d.day - 1)

    @staticmethod
    def _sum_labor(vals: dict[str, float]) -> float:
        return sum(v for k, v in vals.items() if k.endswith("_labor"))

    async def _fetch_day_actuals(
        self, db: AsyncSession, property_id: uuid.UUID, target_date: date,
    ) -> dict[str, float]:
        """Return {line_item_code: value} for a single day."""
        result = await db.execute(
            text("""
                SELECT li.code, da.value
                FROM daily_actuals da
                JOIN line_items li ON li.id = da.line_item_id
                WHERE da.property_id = :property_id
                  AND da.date = :target_date
            """),
            {"property_id": property_id, "target_date": target_date},
        )
        return {row.code: row.value for row in result.fetchall()}

    async def _fetch_prorated_budget(
        self, db: AsyncSession, property_id: uuid.UUID, target_date: date,
    ) -> dict[str, float]:
        """Return prorated daily budget {line_item_code: value} for target_date."""
        year = target_date.year
        month = target_date.month
        days_in_month = calendar.monthrange(year, month)[1]

        result = await db.execute(
            text("""
                SELECT li.code, b.value
                FROM budgets b
                JOIN line_items li ON li.id = b.line_item_id
                WHERE b.property_id = :property_id
                  AND b.year = :year
                  AND b.month = :month
            """),
            {"property_id": property_id, "year": year, "month": month},
        )
        return {row.code: row.value / days_in_month for row in result.fetchall()}
