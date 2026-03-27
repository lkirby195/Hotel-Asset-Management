import calendar
import uuid
from datetime import date, timedelta

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.keys import report_cache_key, report_children_cache_key
from app.models.line_item import LineItem
from app.schemas.common import TimePeriod
from app.schemas.report import InterMonthResponse, PerformanceStatItem, ReportLineItem
from app.services.cache_service import CacheService


# Maps period names to materialized view names
VIEW_MAP = {
    "mtd": "mv_mtd_actuals",
    "qtd": "mv_qtd_actuals",
    "ytd": "mv_ytd_actuals",
    "t28": "mv_trailing_28",
    "weekly": "mv_weekly_actuals",
}

# Deterministic UUIDs for virtual (computed-only) waterfall rows
_CALC_NS = uuid.UUID("00000000-0000-0000-0000-ca1c00000000")
VIRTUAL_IDS = {
    "total_dept_profit": uuid.uuid5(_CALC_NS, "total_dept_profit"),
    "operating_income": uuid.uuid5(_CALC_NS, "operating_income"),
    "ebitda": uuid.uuid5(_CALC_NS, "ebitda"),
    "net_income": uuid.uuid5(_CALC_NS, "net_income"),
}


class ReportService:

    async def get_inter_month(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        property_name: str,
        period: str | TimePeriod,
        start_date: date | None,
        end_date: date | None,
        cache: CacheService | None,
        tenant_id: uuid.UUID,
    ) -> InterMonthResponse:
        today = date.today()
        period_val = period.value if isinstance(period, TimePeriod) else period
        # Map public "monthly" to internal "mtd"
        if period_val == "monthly":
            period_val = "mtd"

        # Determine effective date range for response metadata
        match period_val:
            case "custom" if start_date and end_date:
                eff_start, eff_end = start_date, end_date
            case "daily":
                yesterday = today - timedelta(days=1)
                eff_start = eff_end = start_date or yesterday
            case "mtd" | "monthly":
                eff_start = today.replace(day=1)
                eff_end = today
            case "qtd":
                quarter_month = ((today.month - 1) // 3) * 3 + 1
                eff_start = today.replace(month=quarter_month, day=1)
                eff_end = today
            case "ytd":
                eff_start = today.replace(month=1, day=1)
                eff_end = today
            case "t28":
                eff_start = today - timedelta(days=28)
                eff_end = today
            case "weekly":
                eff_start = today - timedelta(days=today.weekday())
                eff_end = today
            case "rest_of_year":
                if today.month == 12:
                    return InterMonthResponse(
                        property_id=property_id,
                        property_name=property_name,
                        period=period_val,
                        start_date=today,
                        end_date=today,
                        lines=[],
                        note="No remaining months in the current year.",
                    )
                eff_start = date(today.year, today.month + 1, 1)
                eff_end = date(today.year, 12, 31)
            case "annual":
                eff_start = date(today.year, 1, 1)
                eff_end = date(today.year, 12, 31)
            case _:
                eff_start = today.replace(day=1)
                eff_end = today

        # Check cache
        if cache:
            cache_key = report_cache_key(
                str(tenant_id), "inter_month", str(property_id),
                period_val, str(eff_start), str(eff_end),
            )
            cached = await cache.get(cache_key)
            if cached:
                return InterMonthResponse(**cached)

        # Fetch leaf-level actuals from appropriate source
        match period_val:
            case "daily":
                leaf_actuals = await self._fetch_daily_single(db, property_id, eff_start)
            case "rest_of_year":
                leaf_actuals = await self._fetch_rest_of_year(db, property_id)
            case "annual":
                leaf_actuals = await self._fetch_annual(db, property_id)
            case _:
                leaf_actuals = await self._fetch_actuals(db, property_id, period_val, start_date, end_date)

        # Fetch budget data (prorated for the period)
        leaf_budgets = await self._fetch_budget_data(db, property_id, eff_start, eff_end)

        # Fetch prior year data
        leaf_py = await self._fetch_prior_year(db, property_id, eff_start, eff_end)

        # Fetch forecast lock data
        leaf_fl = await self._fetch_forecast_lock(db, property_id, eff_start, eff_end)

        # Roll up leaf values to all ancestor summary items
        actuals = await self._rollup_to_summaries(db, leaf_actuals)
        budget_data = await self._rollup_to_summaries(db, leaf_budgets)
        py_data = await self._rollup_to_summaries(db, leaf_py)
        fl_data = await self._rollup_to_summaries(db, leaf_fl)

        # Compute calculated rows for full USALI waterfall
        await self._compute_calculated_rows(db, actuals, budget_data, py_data, fl_data)

        # Build waterfall lines in USALI order
        lines = await self._build_waterfall_lines(
            db, actuals, budget_data, py_data, fl_data,
        )

        # Fetch performance stats
        performance = await self._fetch_performance_stats(db, actuals)

        response = InterMonthResponse(
            property_id=property_id,
            property_name=property_name,
            period=period_val,
            start_date=eff_start,
            end_date=eff_end,
            lines=lines,
            performance=performance,
        )

        # Cache result
        if cache:
            await cache.set(cache_key, response.model_dump(mode="json"))

        return response

    async def get_children(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        parent_id: uuid.UUID,
        period: str | TimePeriod,
        start_date: date | None,
        end_date: date | None,
        cache: CacheService | None,
        tenant_id: uuid.UUID,
    ) -> list[ReportLineItem]:
        today = date.today()
        period_val = period.value if isinstance(period, TimePeriod) else period
        # Map public "monthly" to internal "mtd"
        if period_val == "monthly":
            period_val = "mtd"

        # Determine effective date range (mirrors get_inter_month)
        match period_val:
            case "custom" if start_date and end_date:
                eff_start, eff_end = start_date, end_date
            case "daily":
                yesterday = today - timedelta(days=1)
                eff_start = eff_end = start_date or yesterday
            case "mtd":
                eff_start = today.replace(day=1)
                eff_end = today
            case "qtd":
                quarter_month = ((today.month - 1) // 3) * 3 + 1
                eff_start = today.replace(month=quarter_month, day=1)
                eff_end = today
            case "ytd":
                eff_start = today.replace(month=1, day=1)
                eff_end = today
            case "t28":
                eff_start = today - timedelta(days=28)
                eff_end = today
            case "weekly":
                eff_start = today - timedelta(days=today.weekday())
                eff_end = today
            case "rest_of_year":
                if today.month == 12:
                    return []
                eff_start = date(today.year, today.month + 1, 1)
                eff_end = date(today.year, 12, 31)
            case "annual":
                eff_start = date(today.year, 1, 1)
                eff_end = date(today.year, 12, 31)
            case _:
                eff_start = today.replace(day=1)
                eff_end = today

        # Check cache
        if cache:
            cache_key = report_children_cache_key(
                str(tenant_id), str(property_id), str(parent_id), period_val,
            )
            cached = await cache.get(cache_key)
            if cached:
                return [ReportLineItem(**item) for item in cached]

        # Fetch leaf-level actuals from appropriate source
        match period_val:
            case "daily":
                leaf_actuals = await self._fetch_daily_single(db, property_id, eff_start)
            case "rest_of_year":
                leaf_actuals = await self._fetch_rest_of_year(db, property_id)
            case "annual":
                leaf_actuals = await self._fetch_annual(db, property_id)
            case _:
                leaf_actuals = await self._fetch_actuals(db, property_id, period_val, start_date, end_date)

        leaf_budgets = await self._fetch_budget_data(db, property_id, eff_start, eff_end)
        leaf_py = await self._fetch_prior_year(db, property_id, eff_start, eff_end)
        leaf_fl = await self._fetch_forecast_lock(db, property_id, eff_start, eff_end)

        actuals = await self._rollup_to_summaries(db, leaf_actuals)
        budget_data = await self._rollup_to_summaries(db, leaf_budgets)
        py_data = await self._rollup_to_summaries(db, leaf_py)
        fl_data = await self._rollup_to_summaries(db, leaf_fl)

        # Compute calculated rows (GOP, NOI) that aren't covered by rollup
        await self._compute_calculated_rows(db, actuals, budget_data, py_data, fl_data)

        child_items = await self._fetch_line_items(db, parent_id=parent_id, summary_only=False)
        lines = self._build_lines(child_items, actuals, budget_data, py_data, fl_data, depth=1)

        if cache:
            await cache.set(
                report_children_cache_key(str(tenant_id), str(property_id), str(parent_id), period_val),
                [line.model_dump(mode="json") for line in lines],
            )

        return lines

    async def _fetch_daily_single(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        target_date: date,
    ) -> dict[uuid.UUID, int]:
        """Returns {line_item_id: value} for a single date from daily_actuals."""
        query = text("""
            SELECT line_item_id, value AS actual_value
            FROM daily_actuals
            WHERE property_id = :property_id
              AND date = :target_date
        """)
        result = await db.execute(query, {
            "property_id": property_id,
            "target_date": target_date,
        })
        return {row.line_item_id: row.actual_value for row in result.fetchall()}

    async def _fetch_rest_of_year(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
    ) -> dict[uuid.UUID, int]:
        """Returns {line_item_id: total_forecast_value} for remaining months of the year.

        Queries forecast_locks for months after the current month through December.
        """
        today = date.today()
        start_month = today.month + 1
        if start_month > 12:
            return {}

        query = text("""
            SELECT line_item_id, SUM(value) AS actual_value
            FROM forecast_locks
            WHERE property_id = :property_id
              AND year = :year
              AND month >= :start_month
              AND month <= 12
            GROUP BY line_item_id
        """)
        result = await db.execute(query, {
            "property_id": property_id,
            "year": today.year,
            "start_month": start_month,
        })
        return {row.line_item_id: row.actual_value for row in result.fetchall()}

    async def _fetch_annual(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
    ) -> dict[uuid.UUID, int]:
        """Returns {line_item_id: combined_value} combining YTD actuals + rest of year forecast."""
        today = date.today()
        ytd_start = date(today.year, 1, 1)

        # Fetch YTD actuals (Jan 1 through today)
        query = text("""
            SELECT line_item_id, SUM(value) AS actual_value
            FROM daily_actuals
            WHERE property_id = :property_id
              AND date >= :start_date AND date <= :end_date
            GROUP BY line_item_id
        """)
        result = await db.execute(query, {
            "property_id": property_id,
            "start_date": ytd_start,
            "end_date": today,
        })
        ytd = {row.line_item_id: row.actual_value for row in result.fetchall()}

        # Fetch rest of year forecast
        rest = await self._fetch_rest_of_year(db, property_id)

        # Merge: sum where both have values
        combined: dict[uuid.UUID, int] = dict(ytd)
        for lid, val in rest.items():
            combined[lid] = combined.get(lid, 0) + val
        return combined

    async def _fetch_actuals(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        period: str,
        start_date: date | None,
        end_date: date | None,
    ) -> dict[uuid.UUID, int]:
        """Returns {line_item_id: actual_value_cents}."""
        if period == "custom" and start_date and end_date:
            query = text("""
                SELECT line_item_id, SUM(value) AS actual_value
                FROM daily_actuals
                WHERE property_id = :property_id
                  AND date >= :start_date AND date <= :end_date
                GROUP BY line_item_id
            """)
            result = await db.execute(query, {
                "property_id": property_id,
                "start_date": start_date,
                "end_date": end_date,
            })
        elif period == "t28":
            query = text("""
                SELECT line_item_id, actual_value
                FROM mv_trailing_28
                WHERE property_id = :property_id
            """)
            result = await db.execute(query, {"property_id": property_id})
        elif period == "weekly":
            # Return current ISO week
            query = text("""
                SELECT line_item_id, actual_value
                FROM mv_weekly_actuals
                WHERE property_id = :property_id
                  AND iso_year = EXTRACT(ISOYEAR FROM CURRENT_DATE)::SMALLINT
                  AND iso_week = EXTRACT(WEEK FROM CURRENT_DATE)::SMALLINT
            """)
            result = await db.execute(query, {"property_id": property_id})
        else:
            view = VIEW_MAP.get(period, "mv_mtd_actuals")
            if period in ("mtd", "qtd"):
                query = text(f"""
                    SELECT line_item_id, actual_value
                    FROM {view}
                    WHERE property_id = :property_id
                      AND year = EXTRACT(YEAR FROM CURRENT_DATE)::SMALLINT
                """)
            else:  # ytd
                query = text(f"""
                    SELECT line_item_id, actual_value
                    FROM {view}
                    WHERE property_id = :property_id
                      AND year = EXTRACT(YEAR FROM CURRENT_DATE)::SMALLINT
                """)
            result = await db.execute(query, {"property_id": property_id})

        rows = result.fetchall()
        return {row.line_item_id: row.actual_value for row in rows}

    async def _fetch_budget_data(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict[uuid.UUID, int]:
        """Returns prorated budget {line_item_id: prorated_budget_cents}.

        Budget is monthly. For partial-month periods, prorate:
        prorated = monthly_budget / days_in_month * days_elapsed
        """
        # Determine which months are covered
        query = text("""
            SELECT line_item_id, year, month, value
            FROM budgets
            WHERE property_id = :property_id
              AND (year * 100 + month) >= :start_ym
              AND (year * 100 + month) <= :end_ym
        """)
        result = await db.execute(query, {
            "property_id": property_id,
            "start_ym": start_date.year * 100 + start_date.month,
            "end_ym": end_date.year * 100 + end_date.month,
        })

        budget_map: dict[uuid.UUID, int] = {}
        for row in result.fetchall():
            days_in_month = calendar.monthrange(row.year, row.month)[1]

            # How many days of this month fall in our range?
            month_start = date(row.year, row.month, 1)
            month_end = date(row.year, row.month, days_in_month)
            range_start = max(month_start, start_date)
            range_end = min(month_end, end_date)
            days_in_range = (range_end - range_start).days + 1

            prorated = int(row.value * days_in_range / days_in_month)
            budget_map[row.line_item_id] = budget_map.get(row.line_item_id, 0) + prorated

        return budget_map

    async def _fetch_forecast_lock(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict[uuid.UUID, int]:
        """Returns prorated forecast lock {line_item_id: prorated_value_cents}.

        Same proration logic as _fetch_budget_data: monthly values are prorated
        for partial months within the date range.
        """
        query = text("""
            SELECT line_item_id, year, month, value
            FROM forecast_locks
            WHERE property_id = :property_id
              AND (year * 100 + month) >= :start_ym
              AND (year * 100 + month) <= :end_ym
        """)
        result = await db.execute(query, {
            "property_id": property_id,
            "start_ym": start_date.year * 100 + start_date.month,
            "end_ym": end_date.year * 100 + end_date.month,
        })

        lock_map: dict[uuid.UUID, int] = {}
        for row in result.fetchall():
            days_in_month = calendar.monthrange(row.year, row.month)[1]

            month_start = date(row.year, row.month, 1)
            month_end = date(row.year, row.month, days_in_month)
            range_start = max(month_start, start_date)
            range_end = min(month_end, end_date)
            days_in_range = (range_end - range_start).days + 1

            prorated = int(row.value * days_in_range / days_in_month)
            lock_map[row.line_item_id] = lock_map.get(row.line_item_id, 0) + prorated

        return lock_map

    async def _fetch_prior_year(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict[uuid.UUID, int]:
        """Returns prior year actuals for the same date range shifted back 1 year."""
        py_start = start_date.replace(year=start_date.year - 1)
        try:
            py_end = end_date.replace(year=end_date.year - 1)
        except ValueError:
            # Feb 29 -> Feb 28
            py_end = end_date.replace(year=end_date.year - 1, day=28)

        query = text("""
            SELECT line_item_id, SUM(value) AS actual_value
            FROM daily_actuals
            WHERE property_id = :property_id
              AND date >= :start_date AND date <= :end_date
            GROUP BY line_item_id
        """)
        result = await db.execute(query, {
            "property_id": property_id,
            "start_date": py_start,
            "end_date": py_end,
        })
        return {row.line_item_id: row.actual_value for row in result.fetchall()}

    async def _rollup_to_summaries(
        self,
        db: AsyncSession,
        leaf_data: dict[uuid.UUID, int],
    ) -> dict[uuid.UUID, int]:
        """Given leaf-level values, roll them up to ancestor summary items.

        Uses a recursive CTE to find all ancestors of each leaf item,
        then sums leaf values into each ancestor.
        Returns a merged dict containing both leaf and summary values.
        """
        if not leaf_data:
            return leaf_data

        # Get the full parent-child mapping
        result = await db.execute(
            select(LineItem.id, LineItem.parent_id)
        )
        rows = result.fetchall()

        # Build child -> parent lookup
        parent_of: dict[uuid.UUID, uuid.UUID | None] = {r.id: r.parent_id for r in rows}

        # For each leaf with data, walk up the tree and accumulate
        rolled: dict[uuid.UUID, int] = dict(leaf_data)
        for leaf_id, value in leaf_data.items():
            current = parent_of.get(leaf_id)
            while current is not None:
                rolled[current] = rolled.get(current, 0) + value
                current = parent_of.get(current)

        return rolled

    async def _compute_calculated_rows(
        self,
        db: AsyncSession,
        actuals: dict[uuid.UUID, int],
        budgets: dict[uuid.UUID, int],
        prior_year: dict[uuid.UUID, int],
        forecast_lock: dict[uuid.UUID, int],
    ) -> None:
        """Compute all USALI waterfall calculated rows and update dicts in-place.

        Total Dept Profit = Total Revenue - Total Dept Expenses
        GOP = Total Dept Profit - Total Undistributed Expenses
        Operating Income = GOP - Management Fee
        EBITDA = Operating Income - (Insurance + Property Tax + Rent)
        NOI = EBITDA (no capital reserve data)
        Net Income = NOI (no below-NOI items)
        """
        calc_codes = [
            "total_revenue", "total_dept_expenses", "total_undist_expenses",
            "total_gop", "total_fixed_charges", "net_operating_income",
            "management_fee", "property_tax", "insurance", "rent_lease",
        ]
        result = await db.execute(
            select(LineItem.id, LineItem.code).where(LineItem.code.in_(calc_codes))
        )
        code_to_id: dict[str, uuid.UUID] = {row.code: row.id for row in result.fetchall()}

        rev_id = code_to_id.get("total_revenue")
        dept_id = code_to_id.get("total_dept_expenses")
        undist_id = code_to_id.get("total_undist_expenses")
        gop_id = code_to_id.get("total_gop")
        noi_id = code_to_id.get("net_operating_income")
        mgmt_id = code_to_id.get("management_fee")
        ptax_id = code_to_id.get("property_tax")
        ins_id = code_to_id.get("insurance")
        rent_id = code_to_id.get("rent_lease")

        if not (rev_id and dept_id and undist_id and gop_id):
            return

        dept_profit_vid = VIRTUAL_IDS["total_dept_profit"]
        op_income_vid = VIRTUAL_IDS["operating_income"]
        ebitda_vid = VIRTUAL_IDS["ebitda"]
        net_income_vid = VIRTUAL_IDS["net_income"]

        for d in (actuals, budgets, prior_year, forecast_lock):
            rev = d.get(rev_id, 0)
            dept = d.get(dept_id, 0)
            undist = d.get(undist_id, 0)

            dept_profit = rev - dept
            d[dept_profit_vid] = dept_profit

            gop = dept_profit - undist
            d[gop_id] = gop

            mgmt = d.get(mgmt_id, 0) if mgmt_id else 0
            op_income = gop - mgmt
            d[op_income_vid] = op_income

            ptax = d.get(ptax_id, 0) if ptax_id else 0
            ins = d.get(ins_id, 0) if ins_id else 0
            rent = d.get(rent_id, 0) if rent_id else 0
            ebitda_val = op_income - ptax - ins - rent
            d[ebitda_vid] = ebitda_val

            if noi_id:
                d[noi_id] = ebitda_val  # NOI = EBITDA when no capital reserve

            d[net_income_vid] = ebitda_val  # Net Income = NOI when no below-NOI items

    async def _fetch_line_items(
        self,
        db: AsyncSession,
        parent_id: uuid.UUID | None,
        summary_only: bool,
    ) -> list[LineItem]:
        """Fetch line items. If parent_id is None, fetch top-level items."""
        stmt = select(LineItem).order_by(LineItem.sort_order)

        if parent_id is None:
            stmt = stmt.where(LineItem.parent_id.is_(None))
        else:
            stmt = stmt.where(LineItem.parent_id == parent_id)

        if summary_only:
            stmt = stmt.where(LineItem.is_summary == True)  # noqa: E712

        result = await db.execute(stmt)
        return list(result.scalars().all())

    def _build_lines(
        self,
        line_items: list[LineItem],
        actuals: dict[uuid.UUID, int],
        budgets: dict[uuid.UUID, int],
        prior_year: dict[uuid.UUID, int],
        forecast_lock: dict[uuid.UUID, int] | None = None,
        depth: int = 0,
    ) -> list[ReportLineItem]:
        lines = []
        for item in line_items:
            actual = actuals.get(item.id, 0)
            budget = budgets.get(item.id, 0)
            py_actual = prior_year.get(item.id)
            fl_value = forecast_lock.get(item.id) if forecast_lock else None

            variance_dollars = actual - budget
            variance_pct = round((variance_dollars / budget) * 100, 2) if budget != 0 else None

            py_variance_dollars = (actual - py_actual) if py_actual is not None else None
            py_variance_pct = (
                round((py_variance_dollars / py_actual) * 100, 2)
                if py_actual is not None and py_actual != 0
                else None
            )

            lines.append(ReportLineItem(
                id=item.id,
                code=item.code,
                name=item.name,
                parent_id=item.parent_id,
                is_summary=item.is_summary,
                data_type=item.data_type,
                sort_order=item.sort_order,
                depth=depth,
                actual=actual,
                budget=budget,
                variance_dollars=variance_dollars,
                variance_pct=variance_pct,
                forecast_lock=fl_value,
                prior_year_actual=py_actual,
                py_variance_dollars=py_variance_dollars,
                py_variance_pct=py_variance_pct,
            ))
        return lines

    # ── Waterfall builder ─────────────────────────────

    async def _build_waterfall_lines(
        self,
        db: AsyncSession,
        actuals: dict[uuid.UUID, int],
        budgets: dict[uuid.UUID, int],
        prior_year: dict[uuid.UUID, int],
        forecast_lock: dict[uuid.UUID, int],
    ) -> list[ReportLineItem]:
        """Build P&L lines in USALI waterfall order."""
        needed = [
            "total_revenue", "total_dept_expenses", "total_undist_expenses",
            "total_gop", "net_operating_income",
            "management_fee", "insurance", "property_tax", "rent_lease",
        ]
        result = await db.execute(
            select(LineItem).where(LineItem.code.in_(needed))
        )
        by_code: dict[str, LineItem] = {i.code: i for i in result.scalars().all()}

        def mk(code: str, sort: int, depth: int = 0, clear_parent: bool = False) -> ReportLineItem | None:
            item = by_code.get(code)
            if not item:
                return None
            return self._make_report_line(
                item, actuals, budgets, prior_year, forecast_lock,
                sort_order=sort, depth=depth, clear_parent=clear_parent,
            )

        def virt(code: str, name: str, sort: int) -> ReportLineItem:
            return self._make_virtual_line(
                VIRTUAL_IDS[code], code, name,
                actuals, budgets, prior_year, forecast_lock,
                sort_order=sort,
            )

        lines: list[ReportLineItem] = []

        # 100: Total Revenue (expandable)
        if line := mk("total_revenue", 100):
            lines.append(line)

        # 200: Total Dept Expenses (expandable)
        if line := mk("total_dept_expenses", 200):
            lines.append(line)

        # 300: Total Dept Profit (calculated)
        lines.append(virt("total_dept_profit", "Total Departmental Profit", 300))

        # 400: Total Undistributed Expenses (expandable)
        if line := mk("total_undist_expenses", 400):
            lines.append(line)

        # 500: GOP (calculated, stored in total_gop)
        if line := mk("total_gop", 500):
            lines.append(line)

        # 510: Management Fee (repositioned from total_fixed_charges)
        if line := mk("management_fee", 510, depth=1, clear_parent=True):
            lines.append(line)

        # 600: Operating Income (calculated)
        lines.append(virt("operating_income", "Operating Income", 600))

        # 610-630: Fixed charge children (repositioned)
        for code, sort in [("insurance", 610), ("property_tax", 620), ("rent_lease", 630)]:
            if line := mk(code, sort, depth=1, clear_parent=True):
                lines.append(line)

        # 700: EBITDA (calculated)
        lines.append(virt("ebitda", "EBITDA", 700))

        # 800: NOI (stored in net_operating_income)
        if line := mk("net_operating_income", 800):
            lines.append(line)

        # 900: Net Income (calculated)
        lines.append(virt("net_income", "Net Income", 900))

        return lines

    def _make_report_line(
        self,
        item: LineItem,
        actuals: dict[uuid.UUID, int],
        budgets: dict[uuid.UUID, int],
        prior_year: dict[uuid.UUID, int],
        forecast_lock: dict[uuid.UUID, int],
        sort_order: int,
        depth: int = 0,
        clear_parent: bool = False,
    ) -> ReportLineItem:
        """Build a ReportLineItem from a DB LineItem."""
        actual = actuals.get(item.id, 0)
        budget = budgets.get(item.id, 0)
        py_actual = prior_year.get(item.id)
        fl_value = forecast_lock.get(item.id) if forecast_lock else None

        variance_dollars = actual - budget
        variance_pct = round((variance_dollars / budget) * 100, 2) if budget != 0 else None
        py_var = (actual - py_actual) if py_actual is not None else None
        py_pct = (
            round((py_var / py_actual) * 100, 2)
            if py_actual is not None and py_actual != 0
            else None
        )

        return ReportLineItem(
            id=item.id,
            code=item.code,
            name=item.name,
            parent_id=None if clear_parent else item.parent_id,
            is_summary=item.is_summary,
            data_type=item.data_type,
            sort_order=sort_order,
            depth=depth,
            actual=actual,
            budget=budget,
            variance_dollars=variance_dollars,
            variance_pct=variance_pct,
            forecast_lock=fl_value,
            prior_year_actual=py_actual,
            py_variance_dollars=py_var,
            py_variance_pct=py_pct,
        )

    def _make_virtual_line(
        self,
        vid: uuid.UUID,
        code: str,
        name: str,
        actuals: dict[uuid.UUID, int],
        budgets: dict[uuid.UUID, int],
        prior_year: dict[uuid.UUID, int],
        forecast_lock: dict[uuid.UUID, int],
        sort_order: int,
        data_type: str = "revenue",
    ) -> ReportLineItem:
        """Build a ReportLineItem for a virtual (computed-only) row."""
        actual = actuals.get(vid, 0)
        budget = budgets.get(vid, 0)
        py_actual = prior_year.get(vid)
        fl_value = forecast_lock.get(vid) if forecast_lock else None

        variance_dollars = actual - budget
        variance_pct = round((variance_dollars / budget) * 100, 2) if budget != 0 else None
        py_var = (actual - py_actual) if py_actual is not None else None
        py_pct = (
            round((py_var / py_actual) * 100, 2)
            if py_actual is not None and py_actual != 0
            else None
        )

        return ReportLineItem(
            id=vid,
            code=code,
            name=name,
            parent_id=None,
            is_summary=True,
            data_type=data_type,
            sort_order=sort_order,
            depth=0,
            actual=actual,
            budget=budget,
            variance_dollars=variance_dollars,
            variance_pct=variance_pct,
            forecast_lock=fl_value,
            prior_year_actual=py_actual,
            py_variance_dollars=py_var,
            py_variance_pct=py_pct,
        )

    # ── Performance stats ─────────────────────────────

    async def _fetch_performance_stats(
        self,
        db: AsyncSession,
        actuals: dict[uuid.UUID, int],
    ) -> list[PerformanceStatItem]:
        """Compute performance statistics from existing stat and revenue items."""
        codes = ["rooms_sold", "available_rooms", "occupied_rooms",
                 "rooms_revenue", "total_revenue"]
        result = await db.execute(
            select(LineItem.id, LineItem.code).where(LineItem.code.in_(codes))
        )
        cid: dict[str, uuid.UUID] = {r.code: r.id for r in result.fetchall()}

        def val(code: str) -> int:
            item_id = cid.get(code)
            return actuals.get(item_id, 0) if item_id else 0

        rooms_sold = val("rooms_sold")
        available = val("available_rooms")
        occupied = val("occupied_rooms")
        rooms_rev = val("rooms_revenue")
        total_rev = val("total_revenue")

        occupancy = round(rooms_sold / available * 100, 1) if available else 0.0
        adr = round(rooms_rev / rooms_sold) if rooms_sold else 0
        revpar = round(rooms_rev / available) if available else 0
        trevpar = round(total_rev / available) if available else 0

        return [
            PerformanceStatItem(label="Rooms Available", value=available, format="integer"),
            PerformanceStatItem(label="Rooms Sold", value=rooms_sold, format="integer"),
            PerformanceStatItem(label="Rooms Occupied", value=occupied, format="integer"),
            PerformanceStatItem(label="Occupancy %", value=occupancy, format="percentage"),
            PerformanceStatItem(label="ADR", value=adr, format="currency"),
            PerformanceStatItem(label="RevPAR", value=revpar, format="currency"),
            PerformanceStatItem(label="TRevPAR", value=trevpar, format="currency"),
        ]
