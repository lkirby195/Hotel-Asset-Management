import calendar
import uuid
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.base import DataSourceAdapter
from app.schemas.dashboard import (
    DeptSnapshotCard,
    DeptSnapshotResponse,
    ForwardLookResponse,
    MTDPaceResponse,
    MTDPaceRow,
    OTBDailyRow,
    OTBSummaryCard,
    YesterdayKPI,
    YesterdayResponse,
)


# Line item codes for the KPIs we need
# room_revenue may be a parent with no actuals — sum children instead
_ROOM_REVENUE_CODES = ["room_revenue", "transient_revenue", "group_revenue", "other_room_revenue"]
_ROOMS_SOLD_CODE = "rooms_sold"
_AVAILABLE_ROOMS_CODE = "available_rooms"


def _sum_room_revenue(vals: dict) -> float:
    """Sum all room revenue codes (parent + children) from a values dict."""
    return sum(vals.get(code, 0) for code in _ROOM_REVENUE_CODES)
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

        room_revenue = _sum_room_revenue(actuals)
        rooms_sold = actuals.get(_ROOMS_SOLD_CODE, 0)
        available_rooms = actuals.get(_AVAILABLE_ROOMS_CODE, 0)
        total_labor = self._sum_labor(actuals)

        occupancy = (rooms_sold / available_rooms) if available_rooms else 0.0
        adr = (room_revenue / rooms_sold) if rooms_sold else 0.0
        revpar = (room_revenue / available_rooms) if available_rooms else 0.0

        stly_room_revenue = stly__sum_room_revenue(actuals)
        stly_rooms_sold = stly_actuals.get(_ROOMS_SOLD_CODE, 0)
        stly_available = stly_actuals.get(_AVAILABLE_ROOMS_CODE, 0)
        stly_labor = self._sum_labor(stly_actuals)
        stly_occupancy = (stly_rooms_sold / stly_available) if stly_available else 0.0
        stly_adr = (stly_room_revenue / stly_rooms_sold) if stly_rooms_sold else 0.0
        stly_revpar = (stly_room_revenue / stly_available) if stly_available else 0.0

        budget_room_rev = _sum_room_revenue(budget_vals)
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
        room_rev = _sum_room_revenue(actuals)
        rooms_sold = actuals.get(_ROOMS_SOLD_CODE, 0)
        available = actuals.get(_AVAILABLE_ROOMS_CODE, 0)
        total_rev = actuals.get(_TOTAL_REVENUE_CODE, 0)
        total_labor = self._sum_labor(actuals)

        occ = (rooms_sold / available) if available else 0.0
        adr = (room_rev / rooms_sold) if rooms_sold else 0.0
        revpar = (room_rev / available) if available else 0.0
        labor_pct = (total_labor / total_rev) if total_rev else 0.0

        b_room_rev = _sum_room_revenue(budget)
        b_rooms_sold = budget.get(_ROOMS_SOLD_CODE, 0)
        b_available = budget.get(_AVAILABLE_ROOMS_CODE, 0)
        b_total_rev = budget.get(_TOTAL_REVENUE_CODE, 0)
        b_labor = self._sum_labor(budget)
        b_occ = (b_rooms_sold / b_available) if b_available else 0.0
        b_adr = (b_room_rev / b_rooms_sold) if b_rooms_sold else 0.0
        b_revpar = (b_room_rev / b_available) if b_available else 0.0
        b_labor_pct = (b_labor / b_total_rev) if b_total_rev else 0.0

        s_room_rev = _sum_room_revenue(stly)
        s_rooms_sold = stly.get(_ROOMS_SOLD_CODE, 0)
        s_available = stly.get(_AVAILABLE_ROOMS_CODE, 0)
        s_total_rev = stly.get(_TOTAL_REVENUE_CODE, 0)
        s_labor = self._sum_labor(stly)
        s_occ = (s_rooms_sold / s_available) if s_available else 0.0
        s_adr = (s_room_rev / s_rooms_sold) if s_rooms_sold else 0.0
        s_revpar = (s_room_rev / s_available) if s_available else 0.0
        s_labor_pct = (s_labor / s_total_rev) if s_total_rev else 0.0

        f_room_rev = _sum_room_revenue(forecast)
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

    # ── Forward Look / OTB ────────────────────────────────────────────

    async def get_forward_look(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        property_name: str,
        property_code: str,
        available_rooms: int,
        adapter: DataSourceAdapter,
        target_date: date | None = None,
    ) -> ForwardLookResponse:
        if target_date is None:
            target_date = date.today()

        end_30 = target_date + timedelta(days=29)

        # Fetch OTB for next 30 days and STLY equivalent
        otb_records = await adapter.fetch_otb([property_code], target_date, end_30)
        stly_start = self._same_day_last_year(target_date)
        stly_end = self._same_day_last_year(end_30)
        stly_records = await adapter.fetch_otb([property_code], stly_start, stly_end)

        # TODO: Pickup requires OTB snapshot history — the adapter needs an as_of_date
        # parameter on fetch_otb to compare today's OTB against the snapshot from 7 days
        # ago. This is a future feature; until then pickup_7day is None on all cards.

        # Index by date
        otb_by_date = {r.date: r for r in otb_records if r.property_code == property_code}
        stly_by_date = {r.date: r for r in stly_records if r.property_code == property_code}

        # Build summary cards
        year = target_date.year
        month = target_date.month
        end_of_month = date(year, month, calendar.monthrange(year, month)[1])
        windows = [
            ("Rest of Month", target_date, min(end_of_month, end_30)),
            ("Next 14 Days", target_date, target_date + timedelta(days=13)),
            ("Next 30 Days", target_date, end_30),
        ]

        summary_cards = []
        for name, w_start, w_end in windows:
            card = self._build_summary_card(
                name, w_start, w_end, otb_by_date, stly_by_date, available_rooms,
            )
            summary_cards.append(card)

        # Build 7-day daily detail
        daily_detail = []
        for i in range(7):
            d = target_date + timedelta(days=i)
            stly_d = self._same_day_last_year(d)
            otb = otb_by_date.get(d)
            stly = stly_by_date.get(stly_d)

            total_rooms = otb.rooms if otb else 0
            revenue = otb.revenue if otb else 0
            adr = otb.adr if otb else 0
            occ = total_rooms / available_rooms if available_rooms else 0.0

            # Mock approximation: 70% transient / 30% group split.
            # In production, OTB data from ProfitSword will include actual
            # segment breakdowns; this fallback is used until that data is available.
            group_rooms = int(total_rooms * 0.30)
            transient_rooms = total_rooms - group_rooms

            stly_rooms = stly.rooms if stly else 0
            stly_revenue = stly.revenue if stly else 0
            vs_stly_pct = (
                round((revenue - stly_revenue) / stly_revenue * 100, 1)
                if stly_revenue else None
            )

            daily_detail.append(OTBDailyRow(
                date=d,
                day_of_week=d.strftime("%a"),
                transient_rooms=transient_rooms,
                group_rooms=group_rooms,
                total_rooms=total_rooms,
                occupancy=round(occ, 4),
                adr=adr,
                revenue=revenue,
                stly_rooms=stly_rooms,
                stly_revenue=stly_revenue,
                vs_stly_pct=vs_stly_pct,
            ))

        return ForwardLookResponse(
            property_id=property_id,
            property_name=property_name,
            as_of_date=target_date,
            available_rooms_per_night=available_rooms,
            summary_cards=summary_cards,
            daily_detail=daily_detail,
        )

    # ── Department Snapshot Cards ────────────────────────────────────

    # Department definitions: revenue/expense line-item codes and KPI specs
    _DEPT_CONFIG = [
        {
            "name": "Rooms",
            "revenue_codes": ["room_revenue", "other_room_revenue"],
            "expense_codes": [
                "rooms_labor", "rooms_ota_commissions", "rooms_supplies", "rooms_other_expense",
            ],
            "kpi1_label": "Margin %",
            "kpi1_type": "margin_pct",
            "kpi2_label": "Labor %",
            "kpi2_type": "labor_pct",
            "labor_code": "rooms_labor",
        },
        {
            "name": "F&B",
            "revenue_codes": ["food_revenue", "beverage_revenue", "catering_revenue"],
            "expense_codes": ["fb_cost_of_sales", "fb_labor", "fb_other_expense"],
            "kpi1_label": "Food Cost %",
            "kpi1_type": "cost_pct",
            "cost_code": "fb_cost_of_sales",
            "kpi2_label": "Labor %",
            "kpi2_type": "labor_pct",
            "labor_code": "fb_labor",
        },
        {
            "name": "Golf",
            "revenue_codes": ["golf_greens_revenue", "golf_cart_revenue", "golf_pro_shop_revenue"],
            "expense_codes": ["golf_labor", "golf_maintenance", "golf_other_expense"],
            "kpi1_label": "Rounds",
            "kpi1_type": "count",
            "count_code": "golf_rounds",
            "kpi2_label": "Rev/Round",
            "kpi2_type": "rev_per_unit",
        },
        {
            "name": "Mountain Ops",
            "revenue_codes": ["mountain_lift_revenue", "mountain_other_revenue"],
            "expense_codes": ["mountain_labor", "mountain_maintenance", "mountain_other_expense"],
            "kpi1_label": "Skier Visits",
            "kpi1_type": "count",
            "count_code": "mountain_skier_visits",
            "kpi2_label": "Rev/Visit",
            "kpi2_type": "rev_per_unit",
        },
        {
            "name": "Spa",
            "revenue_codes": ["spa_services_revenue", "spa_retail_revenue"],
            "expense_codes": ["spa_labor", "spa_cost_of_sales", "spa_other_expense"],
            "kpi1_label": "Treatments",
            "kpi1_type": "count",
            "count_code": "spa_treatments",
            "kpi2_label": "Rev/Treatment",
            "kpi2_type": "rev_per_unit",
        },
        {
            "name": "Retail",
            "revenue_codes": ["retail_revenue"],
            "expense_codes": ["retail_labor", "retail_cost_of_sales", "retail_other_expense"],
            "kpi1_label": "Margin %",
            "kpi1_type": "margin_pct",
            "kpi2_label": "Labor %",
            "kpi2_type": "labor_pct",
            "labor_code": "retail_labor",
        },
    ]

    async def get_dept_snapshots(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        property_name: str,
        period: str = "mtd",
        target_date: date | None = None,
    ) -> DeptSnapshotResponse:
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        period_start, period_end = self._resolve_period_range(period, target_date)
        year = period_start.year
        month = period_start.month
        days_elapsed = (period_end - period_start).days + 1
        days_in_month = calendar.monthrange(year, month)[1]

        actuals = await self._fetch_range_actuals(db, property_id, period_start, period_end)
        budget_vals = await self._fetch_prorated_budget_range(
            db, property_id, year, month, days_in_month, days_elapsed,
        )

        cards = []
        for dept in self._DEPT_CONFIG:
            card = self._build_dept_card(dept, actuals, budget_vals)
            cards.append(card)

        return DeptSnapshotResponse(
            property_id=property_id,
            property_name=property_name,
            period=period,
            cards=cards,
        )

    def _build_dept_card(
        self,
        dept: dict,
        actuals: dict[str, float],
        budget: dict[str, float],
    ) -> DeptSnapshotCard:
        revenue = sum(actuals.get(c, 0) for c in dept["revenue_codes"])
        expenses = sum(actuals.get(c, 0) for c in dept["expense_codes"])
        budget_revenue = sum(budget.get(c, 0) for c in dept["revenue_codes"])

        count_code = dept.get("count_code")
        has_data = (
            revenue != 0
            or expenses != 0
            or (count_code is not None and actuals.get(count_code, 0) != 0)
        )

        variance_pct = None
        if budget_revenue:
            variance_pct = round((revenue - budget_revenue) / budget_revenue * 100, 1)

        kpi1_value = self._compute_dept_kpi(dept, "kpi1", actuals, revenue, expenses)
        kpi2_value = self._compute_dept_kpi(dept, "kpi2", actuals, revenue, expenses)

        return DeptSnapshotCard(
            dept_name=dept["name"],
            revenue=int(revenue),
            budget=int(budget_revenue),
            variance_pct=variance_pct,
            kpi1_label=dept["kpi1_label"],
            kpi1_value=kpi1_value,
            kpi2_label=dept["kpi2_label"],
            kpi2_value=kpi2_value,
            has_data=has_data,
        )

    @staticmethod
    def _compute_dept_kpi(
        dept: dict,
        kpi_key: str,  # "kpi1" or "kpi2"
        actuals: dict[str, float],
        revenue: float,
        expenses: float,
    ) -> str:
        kpi_type = dept[f"{kpi_key}_type"]

        if kpi_type == "margin_pct":
            if not revenue:
                return "0.0%"
            margin = (revenue - expenses) / revenue * 100
            return f"{margin:.1f}%"

        if kpi_type == "labor_pct":
            labor_code = dept.get("labor_code", "")
            labor = actuals.get(labor_code, 0)
            if not revenue:
                return "0.0%"
            pct = labor / revenue * 100
            return f"{pct:.1f}%"

        if kpi_type == "cost_pct":
            cost_code = dept.get("cost_code", "")
            cost = actuals.get(cost_code, 0)
            if not revenue:
                return "0.0%"
            pct = cost / revenue * 100
            return f"{pct:.1f}%"

        if kpi_type == "count":
            count_code = dept.get("count_code", "")
            count = actuals.get(count_code, 0)
            return f"{int(count):,}"

        if kpi_type == "rev_per_unit":
            count_code = dept.get("count_code", "")
            count = actuals.get(count_code, 0)
            if not count:
                return "$0"
            per_unit = revenue / count / 100  # cents to dollars
            return f"${per_unit:,.0f}"

        return "N/A"

    @staticmethod
    def _resolve_period_range(period: str, target_date: date) -> tuple[date, date]:
        """Return (start, end) for the given period string."""
        if period == "mtd":
            return date(target_date.year, target_date.month, 1), target_date
        raise ValueError(f"Unsupported period: {period!r}")

    def _build_summary_card(
        self,
        window_name: str,
        w_start: date,
        w_end: date,
        otb_by_date: dict,
        stly_by_date: dict,
        available: int,
    ) -> OTBSummaryCard:
        nights = (w_end - w_start).days + 1
        total_revenue = 0
        total_rooms = 0
        stly_revenue = 0

        d = w_start
        while d <= w_end:
            otb = otb_by_date.get(d)
            if otb:
                total_revenue += otb.revenue
                total_rooms += otb.rooms

            stly_d = self._same_day_last_year(d)
            stly = stly_by_date.get(stly_d)
            if stly:
                stly_revenue += stly.revenue

            d += timedelta(days=1)

        occ = total_rooms / (available * nights) if (available and nights) else 0.0
        adr = total_revenue // total_rooms if total_rooms else 0
        vs_stly = total_revenue - stly_revenue
        vs_stly_pct = round(vs_stly / stly_revenue * 100, 1) if stly_revenue else None

        return OTBSummaryCard(
            window_name=window_name,
            date_start=w_start,
            date_end=w_end,
            nights=nights,
            otb_revenue=total_revenue,
            otb_occupancy=round(occ, 4),
            otb_adr=adr,
            stly_revenue=stly_revenue,
            vs_stly_revenue=vs_stly,
            vs_stly_pct=vs_stly_pct,
            budget_remaining=None,  # Budget integration deferred
            pickup_7day=None,  # Requires OTB snapshot history (see TODO above)
        )

