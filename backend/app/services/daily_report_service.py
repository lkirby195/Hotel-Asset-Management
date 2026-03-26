import calendar
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.daily_report import DailyReportResponse, DailyReportSection, DualPanelRow


def _to_float(val: object) -> float:
    """Cast Decimal or any numeric DB value to float."""
    if val is None:
        return 0.0
    if isinstance(val, Decimal):
        return float(val)
    return float(val)


class DailyReportService:

    async def get_daily_report(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        property_name: str,
        available_rooms: int,
        target_date: date,
    ) -> DailyReportResponse:
        # Fetch all data sets
        daily = await self._fetch_daily(db, property_id, target_date)
        daily_stly = await self._fetch_daily_stly(db, property_id, target_date)
        daily_forecast = await self._fetch_daily_forecast(db, property_id, target_date)

        mtd_start = target_date.replace(day=1)
        mtd_actual = await self._fetch_mtd_actual(db, property_id, mtd_start, target_date)
        mtd_budget = await self._fetch_mtd_budget(db, property_id, mtd_start, target_date)
        mtd_stly = await self._fetch_mtd_stly(db, property_id, mtd_start, target_date)
        mtd_fcst_lock = await self._fetch_mtd_forecast_lock(db, property_id, mtd_start, target_date)

        # Fetch line items with config for report layout
        line_items = await self._fetch_line_items_with_config(db)

        # Build all 4 tabs — map to actual department_type values in line_items
        tabs: dict[str, list[str]] = {
            "Room Performance": ["rooms"],
            "Ancillary Revenue": ["fb", "spa", "golf", "mountain", "retail"],
            "Labor": [],          # special: labor rows extracted across departments
            "STR Competitive": [],  # placeholder — no seeded data yet
        }

        # Identify labor line items (codes ending in _labor)
        labor_items = [li for li in line_items if li["code"].endswith("_labor")]

        sections: dict[str, list[DailyReportSection]] = {}
        for tab_name, dept_types in tabs.items():
            tab_sections: list[DailyReportSection] = []

            if tab_name == "Labor":
                # Build labor tab from labor line items across all departments
                if labor_items:
                    rows = self._build_rows(
                        labor_items, daily, daily_forecast, daily_stly,
                        mtd_actual, mtd_budget, mtd_stly, mtd_fcst_lock,
                        available_rooms,
                    )
                    tab_sections.append(DailyReportSection(
                        section_name="Labor",
                        rows=rows,
                    ))
            else:
                for dept_type in dept_types:
                    items = [li for li in line_items if li["department_type"] == dept_type]
                    if not items:
                        continue
                    rows = self._build_rows(
                        items, daily, daily_forecast, daily_stly,
                        mtd_actual, mtd_budget, mtd_stly, mtd_fcst_lock,
                        available_rooms,
                    )
                    tab_sections.append(DailyReportSection(
                        section_name=dept_type,
                        rows=rows,
                    ))
            sections[tab_name] = tab_sections

        return DailyReportResponse(
            property_id=property_id,
            property_name=property_name,
            report_date=target_date,
            available_rooms=available_rooms,
            sections=sections,
        )

    def _build_rows(
        self,
        items: list[dict],
        daily: dict[uuid.UUID, float],
        daily_forecast: dict[uuid.UUID, float],
        daily_stly: dict[uuid.UUID, float],
        mtd_actual: dict[uuid.UUID, float],
        mtd_budget: dict[uuid.UUID, float],
        mtd_stly: dict[uuid.UUID, float],
        mtd_fcst_lock: dict[uuid.UUID, float],
        available_rooms: int,
    ) -> list[DualPanelRow]:
        rows: list[DualPanelRow] = []
        for item in items:
            lid = item["id"]
            is_summary = item["is_summary"]
            display_format = item.get("display_format", "currency")

            d_actual = daily.get(lid)
            d_forecast = daily_forecast.get(lid)
            d_stly = daily_stly.get(lid)
            m_actual = mtd_actual.get(lid)
            m_budget = mtd_budget.get(lid)
            m_stly = mtd_stly.get(lid)
            m_fcst = mtd_fcst_lock.get(lid)

            # Variance calculations — use `is not None` (not truthiness)
            d_vs_forecast = None
            if d_actual is not None and d_forecast is not None:
                d_vs_forecast = d_actual - d_forecast

            d_vs_stly = None
            if d_actual is not None and d_stly is not None:
                d_vs_stly = d_actual - d_stly

            m_vs_budget = None
            if m_actual is not None and m_budget is not None:
                m_vs_budget = m_actual - m_budget

            m_vs_stly = None
            if m_actual is not None and m_stly is not None:
                m_vs_stly = m_actual - m_stly

            rows.append(DualPanelRow(
                line_name=item["name"],
                daily_actual=d_actual,
                daily_forecast=d_forecast,
                daily_stly=d_stly,
                daily_vs_forecast=d_vs_forecast,
                daily_vs_stly=d_vs_stly,
                mtd_actual=m_actual,
                mtd_budget=m_budget,
                mtd_stly=m_stly,
                mtd_fcst_lock=m_fcst,
                mtd_vs_budget=m_vs_budget,
                mtd_vs_stly=m_vs_stly,
                is_header=False,
                is_total=is_summary,
                indent=0 if is_summary else 1,
                unit=display_format,
            ))
        return rows

    # ── Data fetchers ──────────────────────────────────────────────

    async def _fetch_daily(
        self, db: AsyncSession, property_id: uuid.UUID, target_date: date,
    ) -> dict[uuid.UUID, float]:
        result = await db.execute(
            text("""
                SELECT line_item_id, value
                FROM daily_actuals
                WHERE property_id = :pid AND date = :d
            """),
            {"pid": property_id, "d": target_date},
        )
        return {row.line_item_id: _to_float(row.value) for row in result.fetchall()}

    async def _fetch_daily_stly(
        self, db: AsyncSession, property_id: uuid.UUID, target_date: date,
    ) -> dict[uuid.UUID, float]:
        try:
            stly_date = target_date.replace(year=target_date.year - 1)
        except ValueError:
            stly_date = target_date.replace(year=target_date.year - 1, day=28)
        result = await db.execute(
            text("""
                SELECT line_item_id, value
                FROM daily_actuals
                WHERE property_id = :pid AND date = :d
            """),
            {"pid": property_id, "d": stly_date},
        )
        return {row.line_item_id: _to_float(row.value) for row in result.fetchall()}

    async def _fetch_daily_forecast(
        self, db: AsyncSession, property_id: uuid.UUID, target_date: date,
    ) -> dict[uuid.UUID, float]:
        """Forecast for a single day = monthly forecast_lock / days_in_month."""
        days_in_month = calendar.monthrange(target_date.year, target_date.month)[1]
        result = await db.execute(
            text("""
                SELECT line_item_id, value
                FROM forecast_locks
                WHERE property_id = :pid
                  AND year = :y AND month = :m
            """),
            {"pid": property_id, "y": target_date.year, "m": target_date.month},
        )
        return {
            row.line_item_id: _to_float(row.value) / days_in_month
            for row in result.fetchall()
        }

    async def _fetch_mtd_actual(
        self, db: AsyncSession, property_id: uuid.UUID,
        start: date, end: date,
    ) -> dict[uuid.UUID, float]:
        result = await db.execute(
            text("""
                SELECT line_item_id, SUM(value) AS total
                FROM daily_actuals
                WHERE property_id = :pid
                  AND date >= :s AND date <= :e
                GROUP BY line_item_id
            """),
            {"pid": property_id, "s": start, "e": end},
        )
        return {row.line_item_id: _to_float(row.total) for row in result.fetchall()}

    async def _fetch_mtd_budget(
        self, db: AsyncSession, property_id: uuid.UUID,
        start: date, end: date,
    ) -> dict[uuid.UUID, float]:
        """Prorated monthly budget for days elapsed in the month."""
        result = await db.execute(
            text("""
                SELECT line_item_id, year, month, value
                FROM budgets
                WHERE property_id = :pid
                  AND (year * 100 + month) >= :start_ym
                  AND (year * 100 + month) <= :end_ym
            """),
            {
                "pid": property_id,
                "start_ym": start.year * 100 + start.month,
                "end_ym": end.year * 100 + end.month,
            },
        )
        budget_map: dict[uuid.UUID, float] = {}
        for row in result.fetchall():
            dim = calendar.monthrange(row.year, row.month)[1]
            month_start = date(row.year, row.month, 1)
            month_end = date(row.year, row.month, dim)
            range_start = max(month_start, start)
            range_end = min(month_end, end)
            days_in_range = (range_end - range_start).days + 1
            prorated = _to_float(row.value) * days_in_range / dim
            budget_map[row.line_item_id] = budget_map.get(row.line_item_id, 0.0) + prorated
        return budget_map

    async def _fetch_mtd_stly(
        self, db: AsyncSession, property_id: uuid.UUID,
        start: date, end: date,
    ) -> dict[uuid.UUID, float]:
        try:
            stly_start = start.replace(year=start.year - 1)
        except ValueError:
            stly_start = start.replace(year=start.year - 1, day=28)
        try:
            stly_end = end.replace(year=end.year - 1)
        except ValueError:
            stly_end = end.replace(year=end.year - 1, day=28)
        result = await db.execute(
            text("""
                SELECT line_item_id, SUM(value) AS total
                FROM daily_actuals
                WHERE property_id = :pid
                  AND date >= :s AND date <= :e
                GROUP BY line_item_id
            """),
            {"pid": property_id, "s": stly_start, "e": stly_end},
        )
        return {row.line_item_id: _to_float(row.total) for row in result.fetchall()}

    async def _fetch_mtd_forecast_lock(
        self, db: AsyncSession, property_id: uuid.UUID,
        start: date, end: date,
    ) -> dict[uuid.UUID, float]:
        """Prorated forecast lock for days elapsed in the month."""
        result = await db.execute(
            text("""
                SELECT line_item_id, year, month, value
                FROM forecast_locks
                WHERE property_id = :pid
                  AND (year * 100 + month) >= :start_ym
                  AND (year * 100 + month) <= :end_ym
            """),
            {
                "pid": property_id,
                "start_ym": start.year * 100 + start.month,
                "end_ym": end.year * 100 + end.month,
            },
        )
        lock_map: dict[uuid.UUID, float] = {}
        for row in result.fetchall():
            dim = calendar.monthrange(row.year, row.month)[1]
            month_start = date(row.year, row.month, 1)
            month_end = date(row.year, row.month, dim)
            range_start = max(month_start, start)
            range_end = min(month_end, end)
            days_in_range = (range_end - range_start).days + 1
            prorated = _to_float(row.value) * days_in_range / dim
            lock_map[row.line_item_id] = lock_map.get(row.line_item_id, 0.0) + prorated
        return lock_map

    async def _fetch_line_items_with_config(
        self, db: AsyncSession,
    ) -> list[dict]:
        """Fetch line items joined with their daily_report config."""
        result = await db.execute(
            text("""
                SELECT li.id, li.code, li.name, li.department_type,
                       li.sort_order, li.is_summary, li.data_type,
                       COALESCE(lic.display_format, 'currency') AS display_format
                FROM line_items li
                LEFT JOIN line_item_config lic
                  ON lic.line_item_id = li.id AND lic.report_type = 'daily_report'
                WHERE li.department_type IS NOT NULL
                ORDER BY li.sort_order
            """),
        )
        items = []
        for row in result.fetchall():
            # Stat items (rooms_sold, covers, etc.) should display as numbers, not currency
            display_format = row.display_format
            if row.data_type == "stat":
                display_format = "number"
            # KPI percentage items
            if row.code in ("occupancy_pct", "gop_margin", "labor_cost_pct"):
                display_format = "percent"
            items.append({
                "id": row.id,
                "code": row.code,
                "name": row.name,
                "department_type": row.department_type,
                "sort_order": row.sort_order,
                "is_summary": row.is_summary,
                "data_type": row.data_type,
                "display_format": display_format,
            })
        return items
