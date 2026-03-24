import calendar
import uuid
from datetime import date, timedelta

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.daily_report import DailyReportResponse, DailyReportSection, DualPanelRow


class DailyReportService:

    async def get_daily_report(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        property_name: str,
        available_rooms: int,
        target_date: date | None = None,
    ) -> DailyReportResponse:
        if target_date is None:
            target_date = date.today() - timedelta(days=1)

        # Date ranges
        year = target_date.year
        month = target_date.month
        mtd_start = date(year, month, 1)
        days_elapsed = (target_date - mtd_start).days + 1
        days_in_month = calendar.monthrange(year, month)[1]

        stly_date = self._same_day_last_year(target_date)
        stly_mtd_start = self._same_day_last_year(mtd_start)

        # Fetch all data
        daily = await self._fetch_day_actuals(db, property_id, target_date)
        daily_stly = await self._fetch_day_actuals(db, property_id, stly_date)
        daily_forecast = await self._fetch_prorated_forecast(db, property_id, target_date)

        mtd = await self._fetch_range_actuals(db, property_id, mtd_start, target_date)
        mtd_stly = await self._fetch_range_actuals(db, property_id, stly_mtd_start, stly_date)
        mtd_budget = await self._fetch_prorated_budget_range(
            db, property_id, year, month, days_in_month, days_elapsed,
        )
        mtd_fcst = await self._fetch_prorated_forecast_range(
            db, property_id, year, month, days_in_month, days_elapsed,
        )

        sections = {
            "Room Performance": self._build_room_performance(
                daily, daily_forecast, daily_stly,
                mtd, mtd_budget, mtd_stly, mtd_fcst,
                available_rooms, days_elapsed,
            ),
            "Ancillary Revenue": self._build_ancillary_revenue(
                daily, daily_forecast, daily_stly,
                mtd, mtd_budget, mtd_stly, mtd_fcst,
            ),
            "Labor": self._build_labor(
                daily, daily_forecast, daily_stly,
                mtd, mtd_budget, mtd_stly, mtd_fcst,
            ),
            "STR Competitive": self._build_str_competitive(),
        }

        return DailyReportResponse(
            property_id=property_id,
            property_name=property_name,
            report_date=target_date,
            available_rooms=available_rooms,
            sections=sections,
        )

    # ── Tab builders ──────────────────────────────────────────────

    def _build_room_performance(
        self,
        daily: dict, daily_fcst: dict, daily_stly: dict,
        mtd: dict, mtd_bgt: dict, mtd_stly: dict, mtd_fcst: dict,
        available_rooms: int, days_elapsed: int,
    ) -> list[DailyReportSection]:
        # Daily derived metrics
        d_sold = daily.get("rooms_sold", 0)
        d_avail = available_rooms
        d_occ = d_sold / d_avail if d_avail else 0.0
        d_rev = daily.get("room_revenue", 0)
        d_adr = d_rev / d_sold if d_sold else 0.0
        d_revpar = d_rev / d_avail if d_avail else 0.0

        df_sold = daily_fcst.get("rooms_sold", 0)
        df_occ = df_sold / d_avail if d_avail else 0.0
        df_rev = daily_fcst.get("room_revenue", 0)
        df_adr = df_rev / df_sold if df_sold else 0.0
        df_revpar = df_rev / d_avail if d_avail else 0.0

        ds_sold = daily_stly.get("rooms_sold", 0)
        ds_occ = ds_sold / d_avail if d_avail else 0.0
        ds_rev = daily_stly.get("room_revenue", 0)
        ds_adr = ds_rev / ds_sold if ds_sold else 0.0
        ds_revpar = ds_rev / d_avail if d_avail else 0.0

        # MTD derived metrics
        m_sold = mtd.get("rooms_sold", 0)
        m_avail = available_rooms * days_elapsed
        m_occ = m_sold / m_avail if m_avail else 0.0
        m_rev = mtd.get("room_revenue", 0)
        m_adr = m_rev / m_sold if m_sold else 0.0
        m_revpar = m_rev / m_avail if m_avail else 0.0

        mb_sold = mtd_bgt.get("rooms_sold", 0)
        mb_occ = mb_sold / m_avail if m_avail else 0.0
        mb_rev = mtd_bgt.get("room_revenue", 0)
        mb_adr = mb_rev / mb_sold if mb_sold else 0.0
        mb_revpar = mb_rev / m_avail if m_avail else 0.0

        ms_sold = mtd_stly.get("rooms_sold", 0)
        ms_occ = ms_sold / m_avail if m_avail else 0.0
        ms_rev = mtd_stly.get("room_revenue", 0)
        ms_adr = ms_rev / ms_sold if ms_sold else 0.0
        ms_revpar = ms_rev / m_avail if m_avail else 0.0

        mf_sold = mtd_fcst.get("rooms_sold", 0)
        mf_occ = mf_sold / m_avail if m_avail else 0.0
        mf_rev = mtd_fcst.get("room_revenue", 0)
        mf_adr = mf_rev / mf_sold if mf_sold else 0.0
        mf_revpar = mf_rev / m_avail if m_avail else 0.0

        occ_rate = DailyReportSection(
            section_name="Occupancy & Rate",
            rows=[
                self._row("Rooms Sold", d_sold, df_sold, ds_sold, m_sold, mb_sold, ms_sold, mf_sold, unit="integer"),
                self._row("Occupancy %", d_occ, df_occ, ds_occ, m_occ, mb_occ, ms_occ, mf_occ, unit="percentage"),
                self._row("ADR", d_adr, df_adr, ds_adr, m_adr, mb_adr, ms_adr, mf_adr, unit="currency"),
                self._row("RevPAR", d_revpar, df_revpar, ds_revpar, m_revpar, mb_revpar, ms_revpar, mf_revpar, unit="currency"),
            ],
        )

        # Segmentation
        d_trans_rooms = daily.get("transient_rooms", 0)
        d_trans_adr = daily.get("transient_adr", 0)
        d_trans_rev = daily.get("transient_revenue", 0)
        d_grp_rooms = daily.get("group_rooms", 0)
        d_grp_adr = daily.get("group_adr", 0)
        d_grp_rev = daily.get("group_revenue", 0)

        df_trans_rooms = daily_fcst.get("transient_rooms", 0)
        df_trans_adr = daily_fcst.get("transient_adr", 0)
        df_trans_rev = daily_fcst.get("transient_revenue", 0)
        df_grp_rooms = daily_fcst.get("group_rooms", 0)
        df_grp_adr = daily_fcst.get("group_adr", 0)
        df_grp_rev = daily_fcst.get("group_revenue", 0)

        ds_trans_rooms = daily_stly.get("transient_rooms", 0)
        ds_trans_adr = daily_stly.get("transient_adr", 0)
        ds_trans_rev = daily_stly.get("transient_revenue", 0)
        ds_grp_rooms = daily_stly.get("group_rooms", 0)
        ds_grp_adr = daily_stly.get("group_adr", 0)
        ds_grp_rev = daily_stly.get("group_revenue", 0)

        m_trans_rooms = mtd.get("transient_rooms", 0)
        m_trans_adr = mtd.get("transient_adr", 0)
        m_trans_rev = mtd.get("transient_revenue", 0)
        m_grp_rooms = mtd.get("group_rooms", 0)
        m_grp_adr = mtd.get("group_adr", 0)
        m_grp_rev = mtd.get("group_revenue", 0)

        mb_trans_rooms = mtd_bgt.get("transient_rooms", 0)
        mb_trans_adr = mtd_bgt.get("transient_adr", 0)
        mb_trans_rev = mtd_bgt.get("transient_revenue", 0)
        mb_grp_rooms = mtd_bgt.get("group_rooms", 0)
        mb_grp_adr = mtd_bgt.get("group_adr", 0)
        mb_grp_rev = mtd_bgt.get("group_revenue", 0)

        ms_trans_rooms = mtd_stly.get("transient_rooms", 0)
        ms_trans_adr = mtd_stly.get("transient_adr", 0)
        ms_trans_rev = mtd_stly.get("transient_revenue", 0)
        ms_grp_rooms = mtd_stly.get("group_rooms", 0)
        ms_grp_adr = mtd_stly.get("group_adr", 0)
        ms_grp_rev = mtd_stly.get("group_revenue", 0)

        mf_trans_rooms = mtd_fcst.get("transient_rooms", 0)
        mf_trans_adr = mtd_fcst.get("transient_adr", 0)
        mf_trans_rev = mtd_fcst.get("transient_revenue", 0)
        mf_grp_rooms = mtd_fcst.get("group_rooms", 0)
        mf_grp_adr = mtd_fcst.get("group_adr", 0)
        mf_grp_rev = mtd_fcst.get("group_revenue", 0)

        segmentation = DailyReportSection(
            section_name="Segmentation",
            rows=[
                self._row("Transient Rooms", d_trans_rooms, df_trans_rooms, ds_trans_rooms, m_trans_rooms, mb_trans_rooms, ms_trans_rooms, mf_trans_rooms, unit="integer", indent=1),
                self._row("Transient ADR", d_trans_adr, df_trans_adr, ds_trans_adr, m_trans_adr, mb_trans_adr, ms_trans_adr, mf_trans_adr, unit="currency", indent=1),
                self._row("Transient Revenue", d_trans_rev, df_trans_rev, ds_trans_rev, m_trans_rev, mb_trans_rev, ms_trans_rev, mf_trans_rev, unit="currency", indent=1),
                self._row("Group Rooms", d_grp_rooms, df_grp_rooms, ds_grp_rooms, m_grp_rooms, mb_grp_rooms, ms_grp_rooms, mf_grp_rooms, unit="integer", indent=1),
                self._row("Group ADR", d_grp_adr, df_grp_adr, ds_grp_adr, m_grp_adr, mb_grp_adr, ms_grp_adr, mf_grp_adr, unit="currency", indent=1),
                self._row("Group Revenue", d_grp_rev, df_grp_rev, ds_grp_rev, m_grp_rev, mb_grp_rev, ms_grp_rev, mf_grp_rev, unit="currency", indent=1),
                self._row("Total Room Revenue", d_rev, df_rev, ds_rev, m_rev, mb_rev, ms_rev, mf_rev, unit="currency", is_total=True),
            ],
        )

        return [occ_rate, segmentation]

    def _build_ancillary_revenue(
        self,
        daily: dict, daily_fcst: dict, daily_stly: dict,
        mtd: dict, mtd_bgt: dict, mtd_stly: dict, mtd_fcst: dict,
    ) -> list[DailyReportSection]:
        fb_codes = [
            ("Restaurant", "restaurant_revenue"),
            ("Bar / Lounge", "bar_revenue"),
            ("Banquet / Catering", "catering_revenue"),
            ("In-Room Dining", "ird_revenue"),
        ]

        fb_rows = []
        d_fb_total = 0
        df_fb_total = 0
        ds_fb_total = 0
        m_fb_total = 0
        mb_fb_total = 0
        ms_fb_total = 0
        mf_fb_total = 0

        for label, code in fb_codes:
            d = daily.get(code, 0)
            df = daily_fcst.get(code, 0)
            ds = daily_stly.get(code, 0)
            m = mtd.get(code, 0)
            mb = mtd_bgt.get(code, 0)
            ms = mtd_stly.get(code, 0)
            mf = mtd_fcst.get(code, 0)
            d_fb_total += d
            df_fb_total += df
            ds_fb_total += ds
            m_fb_total += m
            mb_fb_total += mb
            ms_fb_total += ms
            mf_fb_total += mf
            fb_rows.append(self._row(label, d, df, ds, m, mb, ms, mf, indent=1))

        fb_rows.append(self._row("Total F&B", d_fb_total, df_fb_total, ds_fb_total, m_fb_total, mb_fb_total, ms_fb_total, mf_fb_total, is_total=True))

        # F&B per occupied room
        d_sold = daily.get("rooms_sold", 0)
        m_sold = mtd.get("rooms_sold", 0)
        d_fb_por = d_fb_total / d_sold if d_sold else 0
        df_sold = daily_fcst.get("rooms_sold", 0)
        df_fb_por = df_fb_total / df_sold if df_sold else 0
        ds_sold = daily_stly.get("rooms_sold", 0)
        ds_fb_por = ds_fb_total / ds_sold if ds_sold else 0
        m_fb_por = m_fb_total / m_sold if m_sold else 0
        mb_sold = mtd_bgt.get("rooms_sold", 0)
        mb_fb_por = mb_fb_total / mb_sold if mb_sold else 0
        ms_sold = mtd_stly.get("rooms_sold", 0)
        ms_fb_por = ms_fb_total / ms_sold if ms_sold else 0
        mf_sold = mtd_fcst.get("rooms_sold", 0)
        mf_fb_por = mf_fb_total / mf_sold if mf_sold else 0
        fb_rows.append(self._row("F&B per Occupied Room", d_fb_por, df_fb_por, ds_fb_por, m_fb_por, mb_fb_por, ms_fb_por, mf_fb_por, indent=1))

        fb_section = DailyReportSection(section_name="F&B", rows=fb_rows)

        other_codes = [
            ("Golf", "golf_revenue"),
            ("Mountain Ops", "mountain_revenue"),
            ("Spa", "spa_revenue"),
            ("Retail", "retail_revenue"),
            ("Parking / Valet", "parking_revenue"),
            ("Resort Fees", "resort_fee_revenue"),
        ]

        other_rows = []
        d_other_total = 0
        df_other_total = 0
        ds_other_total = 0
        m_other_total = 0
        mb_other_total = 0
        ms_other_total = 0
        mf_other_total = 0

        for label, code in other_codes:
            d = daily.get(code, 0)
            df = daily_fcst.get(code, 0)
            ds = daily_stly.get(code, 0)
            m = mtd.get(code, 0)
            mb = mtd_bgt.get(code, 0)
            ms = mtd_stly.get(code, 0)
            mf = mtd_fcst.get(code, 0)
            d_other_total += d
            df_other_total += df
            ds_other_total += ds
            m_other_total += m
            mb_other_total += mb
            ms_other_total += ms
            mf_other_total += mf
            other_rows.append(self._row(label, d, df, ds, m, mb, ms, mf, indent=1))

        other_rows.append(self._row("Total Other Revenue", d_other_total, df_other_total, ds_other_total, m_other_total, mb_other_total, ms_other_total, mf_other_total, is_total=True))

        other_section = DailyReportSection(section_name="Other Revenue", rows=other_rows)

        return [fb_section, other_section]

    def _build_labor(
        self,
        daily: dict, daily_fcst: dict, daily_stly: dict,
        mtd: dict, mtd_bgt: dict, mtd_stly: dict, mtd_fcst: dict,
    ) -> list[DailyReportSection]:
        depts = [
            ("Rooms", "rooms"),
            ("F&B", "fb"),
            ("Spa", "spa"),
            ("Golf", "golf"),
            ("Mountain Ops", "mountain"),
            ("A&G", "ag"),
            ("Maintenance", "maintenance"),
        ]

        sections = []
        d_total_wages = 0
        df_total_wages = 0
        ds_total_wages = 0
        m_total_wages = 0
        mb_total_wages = 0
        ms_total_wages = 0
        mf_total_wages = 0
        d_total_hours = 0
        m_total_hours = 0

        for dept_label, prefix in depts:
            wages_code = f"{prefix}_labor"
            hours_code = f"{prefix}_labor_hours"

            d_w = daily.get(wages_code, 0)
            d_h = daily.get(hours_code, 0)
            d_rate = d_w / d_h if d_h else 0
            df_w = daily_fcst.get(wages_code, 0)
            df_h = daily_fcst.get(hours_code, 0)
            df_rate = df_w / df_h if df_h else 0
            ds_w = daily_stly.get(wages_code, 0)
            ds_h = daily_stly.get(hours_code, 0)
            ds_rate = ds_w / ds_h if ds_h else 0

            m_w = mtd.get(wages_code, 0)
            m_h = mtd.get(hours_code, 0)
            mb_w = mtd_bgt.get(wages_code, 0)
            mb_h = mtd_bgt.get(hours_code, 0)
            ms_w = mtd_stly.get(wages_code, 0)
            ms_h = mtd_stly.get(hours_code, 0)
            mf_w = mtd_fcst.get(wages_code, 0)
            mf_h = mtd_fcst.get(hours_code, 0)

            # Track totals
            d_total_wages += d_w
            df_total_wages += df_w
            ds_total_wages += ds_w
            m_total_wages += m_w
            mb_total_wages += mb_w
            ms_total_wages += ms_w
            mf_total_wages += mf_w
            d_total_hours += d_h
            m_total_hours += m_h

            # MTD total revenue for % of revenue calc
            m_total_rev = mtd.get("total_revenue", 0)
            m_rev_pct = m_w / m_total_rev if m_total_rev else 0
            mb_total_rev = mtd_bgt.get("total_revenue", 0)
            mb_rev_pct = mb_w / mb_total_rev if mb_total_rev else 0

            rows = [
                DualPanelRow(line_name=dept_label, is_header=True, unit="currency"),
                self._row("Wages", d_w, df_w, ds_w, m_w, mb_w, ms_w, mf_w, indent=1),
                self._row("Hours", d_h, df_h, ds_h, m_h, mb_h, ms_h, mf_h, unit="decimal", indent=1),
                self._row("$/Hour", d_rate, df_rate, ds_rate,
                          m_w / m_h if m_h else 0, mb_w / mb_h if mb_h else 0,
                          ms_w / ms_h if ms_h else 0, mf_w / mf_h if mf_h else 0,
                          unit="currency", indent=1),
            ]
            sections.append(DailyReportSection(section_name=dept_label, rows=rows))

        # Total Labor section
        m_total_rev = mtd.get("total_revenue", 0)
        d_sold = daily.get("rooms_sold", 0)
        m_sold = mtd.get("rooms_sold", 0)

        total_rows = [
            self._row("Total Labor Wages", d_total_wages, df_total_wages, ds_total_wages, m_total_wages, mb_total_wages, ms_total_wages, mf_total_wages, is_total=True),
            self._row("FTEs", d_total_hours / 8 if d_total_hours else 0, 0, 0,
                       m_total_hours / 8 if m_total_hours else 0, 0, 0, 0, unit="decimal", indent=1),
            self._row("MPOR", d_total_wages / d_sold if d_sold else 0, 0, 0,
                       m_total_wages / m_sold if m_sold else 0, 0, 0, 0, unit="currency", indent=1),
            self._row("Labor %", d_total_wages / daily.get("total_revenue", 1) if daily.get("total_revenue") else 0, 0, 0,
                       m_total_wages / m_total_rev if m_total_rev else 0, 0, 0, 0, unit="percentage", indent=1),
            self._row("Hrs / Occ Room", d_total_hours / d_sold if d_sold else 0, 0, 0,
                       m_total_hours / m_sold if m_sold else 0, 0, 0, 0, unit="decimal", indent=1),
        ]

        sections.append(DailyReportSection(section_name="Total Labor", rows=total_rows))
        return sections

    def _build_str_competitive(self) -> list[DailyReportSection]:
        return [
            DailyReportSection(
                section_name="STR Competitive Set",
                rows=[
                    self._row("Occupancy Index", None, None, None, None, None, None, None, unit="decimal"),
                    self._row("ADR Index", None, None, None, None, None, None, None, unit="decimal"),
                    self._row("RevPAR Index", None, None, None, None, None, None, None, unit="decimal"),
                ],
            )
        ]

    # ── Row helper ────────────────────────────────────────────────

    @staticmethod
    def _row(
        name: str,
        d_actual: float, d_forecast: float, d_stly: float,
        m_actual: float, m_budget: float, m_stly: float, m_fcst: float,
        unit: str = "currency",
        indent: int = 0,
        is_total: bool = False,
    ) -> DualPanelRow:
        d_vs_fcst = d_actual - d_forecast if d_actual is not None and d_forecast is not None else None
        d_vs_stly = d_actual - d_stly if d_actual is not None and d_stly is not None else None
        m_vs_bgt = m_actual - m_budget if m_actual is not None and m_budget is not None else None
        m_vs_stly = m_actual - m_stly if m_actual is not None and m_stly is not None else None

        return DualPanelRow(
            line_name=name,
            daily_actual=round(d_actual, 2) if d_actual is not None else d_actual,
            daily_forecast=round(d_forecast, 2) if d_forecast is not None else d_forecast,
            daily_stly=round(d_stly, 2) if d_stly is not None else d_stly,
            daily_vs_forecast=round(d_vs_fcst, 2) if d_vs_fcst is not None else d_vs_fcst,
            daily_vs_stly=round(d_vs_stly, 2) if d_vs_stly is not None else d_vs_stly,
            mtd_actual=round(m_actual, 2) if m_actual is not None else m_actual,
            mtd_budget=round(m_budget, 2) if m_budget is not None else m_budget,
            mtd_stly=round(m_stly, 2) if m_stly is not None else m_stly,
            mtd_fcst_lock=round(m_fcst, 2) if m_fcst is not None else m_fcst,
            mtd_vs_budget=round(m_vs_bgt, 2) if m_vs_bgt is not None else m_vs_bgt,
            mtd_vs_stly=round(m_vs_stly, 2) if m_vs_stly is not None else m_vs_stly,
            is_header=False,
            is_total=is_total,
            indent=indent,
            unit=unit,
        )

    # ── Data fetching ─────────────────────────────────────────────

    @staticmethod
    def _same_day_last_year(d: date) -> date:
        try:
            return d.replace(year=d.year - 1)
        except ValueError:
            return d.replace(year=d.year - 1, day=d.day - 1)

    async def _fetch_day_actuals(
        self, db: AsyncSession, property_id: uuid.UUID, target_date: date,
    ) -> dict[str, float]:
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

    async def _fetch_range_actuals(
        self, db: AsyncSession, property_id: uuid.UUID, start_date: date, end_date: date,
    ) -> dict[str, float]:
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

    async def _fetch_prorated_forecast(
        self, db: AsyncSession, property_id: uuid.UUID, target_date: date,
    ) -> dict[str, float]:
        year = target_date.year
        month = target_date.month
        days_in_month = calendar.monthrange(year, month)[1]

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
        return {row.code: row.value / days_in_month for row in result.fetchall()}

    async def _fetch_prorated_budget_range(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        year: int,
        month: int,
        days_in_month: int,
        days_elapsed: int,
    ) -> dict[str, float]:
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
