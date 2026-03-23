import calendar
import uuid
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.dashboard import MTDPaceResponse, MTDPaceRow, YesterdayKPI, YesterdayResponse


# Line item codes for the KPIs we need
_REVENUE_CODE = "room_revenue"
_ROOMS_SOLD_CODE = "rooms_sold"
_AVAILABLE_ROOMS_CODE = "available_rooms"
_TOTAL_REVENUE_CODE = "total_revenue"
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

    # ── MTD Pace ──────────────────────────────────────────────────────

    async def get_mtd_pace(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        property_name: str,
        target_date: date | None = None,
    ) -> MTDPaceResponse:
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        year = target_date.year
        month = target_date.month
        period_start = date(year, month, 1)
        period_end = target_date
        days_elapsed = (period_end - period_start).days + 1
        days_in_month = calendar.monthrange(year, month)[1]

        actuals = await self._fetch_range_actuals(db, property_id, period_start, period_end)

        stly_start = self._same_day_last_year(period_start)
        stly_end = self._same_day_last_year(period_end)
        stly_actuals = await self._fetch_range_actuals(db, property_id, stly_start, stly_end)

        budget_vals = await self._fetch_prorated_budget_range(
            db, property_id, year, month, days_in_month, days_elapsed,
        )
        forecast_vals = await self._fetch_prorated_forecast_range(
            db, property_id, year, month, days_in_month, days_elapsed,
        )

        rows = self._build_mtd_rows(actuals, budget_vals, stly_actuals, forecast_vals)

        return MTDPaceResponse(
            property_id=property_id,
            property_name=property_name,
            period_start=period_start,
            period_end=period_end,
            days_elapsed=days_elapsed,
            days_in_month=days_in_month,
            rows=rows,
        )

    def _build_mtd_rows(
        self,
        actuals: dict[str, float],
        budget: dict[str, float],
        stly: dict[str, float],
        forecast: dict[str, float],
    ) -> list[MTDPaceRow]:
        room_rev = actuals.get(_REVENUE_CODE, 0)
        rooms_sold = actuals.get(_ROOMS_SOLD_CODE, 0)
        available = actuals.get(_AVAILABLE_ROOMS_CODE, 0)
        total_rev = actuals.get(_TOTAL_REVENUE_CODE, 0)
        total_labor = self._sum_labor(actuals)

        occ = (rooms_sold / available) if available else 0.0
        adr = (room_rev / rooms_sold) if rooms_sold else 0.0
        revpar = (room_rev / available) if available else 0.0
        labor_pct = (total_labor / total_rev) if total_rev else 0.0

        b_room_rev = budget.get(_REVENUE_CODE, 0)
        b_rooms_sold = budget.get(_ROOMS_SOLD_CODE, 0)
        b_available = budget.get(_AVAILABLE_ROOMS_CODE, 0)
        b_total_rev = budget.get(_TOTAL_REVENUE_CODE, 0)
        b_labor = self._sum_labor(budget)
        b_occ = (b_rooms_sold / b_available) if b_available else 0.0
        b_adr = (b_room_rev / b_rooms_sold) if b_rooms_sold else 0.0
        b_revpar = (b_room_rev / b_available) if b_available else 0.0
        b_labor_pct = (b_labor / b_total_rev) if b_total_rev else 0.0

        s_room_rev = stly.get(_REVENUE_CODE, 0)
        s_rooms_sold = stly.get(_ROOMS_SOLD_CODE, 0)
        s_available = stly.get(_AVAILABLE_ROOMS_CODE, 0)
        s_total_rev = stly.get(_TOTAL_REVENUE_CODE, 0)
        s_labor = self._sum_labor(stly)
        s_occ = (s_rooms_sold / s_available) if s_available else 0.0
        s_adr = (s_room_rev / s_rooms_sold) if s_rooms_sold else 0.0
        s_revpar = (s_room_rev / s_available) if s_available else 0.0
        s_labor_pct = (s_labor / s_total_rev) if s_total_rev else 0.0

        f_room_rev = forecast.get(_REVENUE_CODE, 0)
        f_rooms_sold = forecast.get(_ROOMS_SOLD_CODE, 0)
        f_available = forecast.get(_AVAILABLE_ROOMS_CODE, 0)
        f_total_rev = forecast.get(_TOTAL_REVENUE_CODE, 0)
        f_labor = self._sum_labor(forecast)
        f_occ = (f_rooms_sold / f_available) if f_available else 0.0
        f_adr = (f_room_rev / f_rooms_sold) if f_rooms_sold else 0.0
        f_revpar = (f_room_rev / f_available) if f_available else 0.0
        f_labor_pct = (f_labor / f_total_rev) if f_total_rev else 0.0

        return [
            self._make_pace_row("Occupancy", occ, b_occ, s_occ, f_occ, "percentage"),
            self._make_pace_row("ADR", adr, b_adr, s_adr, f_adr, "currency"),
            self._make_pace_row("RevPAR", revpar, b_revpar, s_revpar, f_revpar, "currency"),
            self._make_pace_row("Room Revenue", room_rev, b_room_rev, s_room_rev, f_room_rev, "currency"),
            self._make_pace_row("Total Revenue", total_rev, b_total_rev, s_total_rev, f_total_rev, "currency"),
            self._make_pace_row("Total Labor", total_labor, b_labor, s_labor, f_labor, "currency"),
            self._make_pace_row("Labor % of Revenue", labor_pct, b_labor_pct, s_labor_pct, f_labor_pct, "percentage"),
        ]

    @staticmethod
    def _make_pace_row(
        name: str,
        actual: float,
        budget: float,
        stly: float,
        forecast_lock: float,
        unit: str,
    ) -> MTDPaceRow:
        vs_budget = actual - budget
        vs_stly = actual - stly
        vs_forecast = actual - forecast_lock
        vs_budget_pct = (vs_budget / budget * 100) if budget else None
        vs_stly_pct = (vs_stly / stly * 100) if stly else None
        return MTDPaceRow(
            metric_name=name,
            actual=actual,
            budget=budget,
            stly=stly,
            forecast_lock=forecast_lock,
            vs_budget=vs_budget,
            vs_budget_pct=round(vs_budget_pct, 1) if vs_budget_pct is not None else None,
            vs_stly=vs_stly,
            vs_stly_pct=round(vs_stly_pct, 1) if vs_stly_pct is not None else None,
            vs_forecast=vs_forecast,
            unit=unit,
        )

    async def _fetch_range_actuals(
        self, db: AsyncSession, property_id: uuid.UUID, start_date: date, end_date: date,
    ) -> dict[str, float]:
        """Return {line_item_code: summed_value} for a date range."""
        result = await db.execute(
            text("""
                SELECT li.code, SUM(da.value) AS value
                FROM daily_actuals da
                JOIN line_items li ON li.id = da.line_item_id
                WHERE da.property_id = :property_id
                  AND da.date >= :start_date
                  AND da.date <= :end_date
                GROUP BY li.code
            """),
            {"property_id": property_id, "start_date": start_date, "end_date": end_date},
        )
        return {row.code: row.value for row in result.fetchall()}

    async def _fetch_prorated_budget_range(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        year: int,
        month: int,
        days_in_month: int,
        days_elapsed: int,
    ) -> dict[str, float]:
        """Return budget prorated to days_elapsed {code: value}."""
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
        return {row.code: row.value * days_elapsed / days_in_month for row in result.fetchall()}

    async def _fetch_prorated_forecast_range(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        year: int,
        month: int,
        days_in_month: int,
        days_elapsed: int,
    ) -> dict[str, float]:
        """Return forecast lock prorated to days_elapsed {code: value}."""
        result = await db.execute(
            text("""
                SELECT li.code, fl.value
                FROM forecast_locks fl
                JOIN line_items li ON li.id = fl.line_item_id
                WHERE fl.property_id = :property_id
                  AND fl.year = :year
                  AND fl.month = :month
            """),
            {"property_id": property_id, "year": year, "month": month},
        )
        return {row.code: row.value * days_elapsed / days_in_month for row in result.fetchall()}
