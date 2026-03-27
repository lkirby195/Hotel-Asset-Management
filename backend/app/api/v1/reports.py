import uuid
from datetime import date

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import get_redis
from app.dependencies import get_current_user, get_db_session, require_property_access
from app.models.month_close import MonthCloseStatus
from app.models.user import User
from app.schemas.common import APIResponse, TimePeriod
from app.schemas.dept_detail import DeptDetailResponse, DeptKPI, DeptPLLine
from app.schemas.report import InterMonthResponse, PLKPIResponse, ReportLineItem
from app.services.cache_service import CacheService
from app.services.property_service import PropertyService
from app.services.report_service import ReportService

router = APIRouter()
report_service = ReportService()
property_service = PropertyService()


# ── Department detail configuration ──────────────────────────────

_DEPT_TYPE_MAP: dict[str, dict] = {
    "rooms": {
        "name": "Rooms",
        "revenue_codes": ["room_revenue", "transient_revenue", "group_revenue", "other_room_revenue"],
        "expense_codes": [
            "rooms_labor", "rooms_ota_commissions", "rooms_supplies", "rooms_other_expense",
        ],
        "count_code": "rooms_sold",
        "available_code": "available_rooms",
        "labor_code": "rooms_labor",
    },
    "fb": {
        "name": "Food & Beverage",
        "revenue_codes": ["food_revenue", "beverage_revenue", "catering_revenue"],
        "expense_codes": ["fb_cost_of_sales", "fb_labor", "fb_other_expense"],
        "food_cost_code": "fb_cost_of_sales",
        "bev_cost_code": "fb_cost_of_sales",
        "labor_code": "fb_labor",
        "covers_code": "fb_covers",
        "rooms_sold_code": "rooms_sold",
    },
    "golf": {
        "name": "Golf",
        "revenue_codes": ["golf_greens_revenue", "golf_cart_revenue", "golf_pro_shop_revenue"],
        "expense_codes": ["golf_labor", "golf_maintenance", "golf_other_expense"],
        "count_code": "golf_rounds",
        "cart_code": "golf_cart_revenue",
        "pro_shop_code": "golf_pro_shop_revenue",
        "labor_code": "golf_labor",
    },
    "mountain": {
        "name": "Mountain Operations",
        "revenue_codes": ["mountain_lift_revenue", "mountain_rental_revenue", "mountain_lessons_revenue", "mountain_summer_revenue"],
        "expense_codes": ["mountain_labor", "mountain_snowmaking", "mountain_other_expense"],
        "count_code": "mountain_skier_visits",
        "lift_code": "mountain_lift_revenue",
        "rental_code": "mountain_rental_revenue",
        "lessons_code": "mountain_lessons_revenue",
        "snowmaking_code": "mountain_snowmaking",
    },
    "spa": {
        "name": "Spa",
        "revenue_codes": ["spa_services_revenue", "spa_retail_revenue"],
        "expense_codes": ["spa_labor", "spa_cost_of_sales", "spa_other_expense"],
        "count_code": "spa_treatments",
        "services_code": "spa_services_revenue",
        "retail_code": "spa_retail_revenue",
        "labor_code": "spa_labor",
        "capacity_code": "spa_capacity",
    },
    "retail": {
        "name": "Retail",
        "revenue_codes": ["retail_revenue"],
        "expense_codes": ["retail_labor", "retail_cost_of_sales", "retail_other_expense"],
        "labor_code": "retail_labor",
        "cogs_code": "retail_cost_of_sales",
    },
}


@router.get(
    "/inter-month/{property_id}",
    response_model=APIResponse[InterMonthResponse],
)
async def inter_month_report(
    property_id: uuid.UUID = Depends(require_property_access),
    period: TimePeriod = Query(default=TimePeriod.monthly),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis),
):

    if period == TimePeriod.custom and (not start or not end):
        raise HTTPException(status_code=400, detail="Custom period requires start and end dates")

    prop = await property_service.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    cache = CacheService(redis_client)
    report = await report_service.get_inter_month(
        db=db,
        property_id=property_id,
        property_name=prop.name,
        period=period,
        start_date=start,
        end_date=end,
        cache=cache,
        tenant_id=current_user.tenant_id,
    )
    return APIResponse(data=report)


@router.get(
    "/inter-month/{property_id}/children/{parent_id}",
    response_model=APIResponse[list[ReportLineItem]],
)
async def inter_month_children(
    parent_id: uuid.UUID,
    property_id: uuid.UUID = Depends(require_property_access),
    period: TimePeriod = Query(default=TimePeriod.monthly),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis),
):
    cache = CacheService(redis_client)
    children = await report_service.get_children(
        db=db,
        property_id=property_id,
        parent_id=parent_id,
        period=period,
        start_date=start,
        end_date=end,
        cache=cache,
        tenant_id=current_user.tenant_id,
    )
    return APIResponse(data=children)


_ROOM_REVENUE_CODES = ["room_revenue", "transient_revenue", "group_revenue", "other_room_revenue"]
_ROOMS_SOLD_CODE = "rooms_sold"


@router.get(
    "/pl-kpis/{property_id}",
    response_model=APIResponse[PLKPIResponse],
)
async def pl_kpis(
    property_id: uuid.UUID = Depends(require_property_access),
    start: date = Query(...),
    end: date = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis),
):
    import calendar as _cal

    from sqlalchemy import text as sa_text

    prop = await property_service.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    cache = CacheService(redis_client)

    # Reuse report_service for the full P&L rollup (gives us GOP, NOI, EBITDA, total_revenue)
    report = await report_service.get_inter_month(
        db=db,
        property_id=property_id,
        property_name=prop.name,
        period="custom",
        start_date=start,
        end_date=end,
        cache=cache,
        tenant_id=current_user.tenant_id,
    )

    # Build code->line lookup from report lines
    by_code = {line.code: line for line in report.lines}

    all_codes = [_ROOMS_SOLD_CODE] + _ROOM_REVENUE_CODES

    # Fetch rooms_sold and room_revenue components from daily_actuals by code
    result = await db.execute(
        sa_text("""
            SELECT li.code, SUM(da.value) AS total
            FROM daily_actuals da
            JOIN line_items li ON li.id = da.line_item_id
            WHERE da.property_id = :property_id
              AND da.date >= :start_date AND da.date <= :end_date
              AND li.code = ANY(:codes)
            GROUP BY li.code
        """),
        {
            "property_id": property_id,
            "start_date": start,
            "end_date": end,
            "codes": all_codes,
        },
    )
    code_vals = {row.code: row.total for row in result.fetchall()}

    rooms_sold = code_vals.get(_ROOMS_SOLD_CODE, 0)
    room_revenue = sum(code_vals.get(c, 0) for c in _ROOM_REVENUE_CODES)

    # Available rooms = property.available_rooms * days in range
    days_in_range = (end - start).days + 1
    avail_rooms = (prop.available_rooms or 0) * days_in_range

    occupancy = (rooms_sold / avail_rooms) if avail_rooms else 0.0
    adr = int(room_revenue / rooms_sold) if rooms_sold else 0
    revpar = int(room_revenue / avail_rooms) if avail_rooms else 0

    # Budget versions of rooms_sold and room_revenue (prorated)
    budget_result = await db.execute(
        sa_text("""
            SELECT li.code, b.year, b.month, b.value
            FROM budgets b
            JOIN line_items li ON li.id = b.line_item_id
            WHERE b.property_id = :property_id
              AND (b.year * 100 + b.month) >= :start_ym
              AND (b.year * 100 + b.month) <= :end_ym
              AND li.code = ANY(:codes)
        """),
        {
            "property_id": property_id,
            "start_ym": start.year * 100 + start.month,
            "end_ym": end.year * 100 + end.month,
            "codes": all_codes,
        },
    )
    budget_code_vals: dict[str, float] = {}
    for row in budget_result.fetchall():
        dim = _cal.monthrange(row.year, row.month)[1]
        m_start = date(row.year, row.month, 1)
        m_end = date(row.year, row.month, dim)
        r_start = max(m_start, start)
        r_end = min(m_end, end)
        days = (r_end - r_start).days + 1
        prorated = row.value * days / dim
        budget_code_vals[row.code] = budget_code_vals.get(row.code, 0) + prorated

    bgt_rooms_sold = budget_code_vals.get(_ROOMS_SOLD_CODE, 0)
    bgt_room_revenue = sum(budget_code_vals.get(c, 0) for c in _ROOM_REVENUE_CODES)
    bgt_occupancy = (bgt_rooms_sold / avail_rooms) if avail_rooms else 0.0
    bgt_adr = int(bgt_room_revenue / bgt_rooms_sold) if bgt_rooms_sold else 0
    bgt_revpar = int(bgt_room_revenue / avail_rooms) if avail_rooms else 0

    # Extract totals from report lines
    total_rev_line = by_code.get("total_revenue")
    gop_line = by_code.get("total_gop")
    noi_line = by_code.get("noi") or by_code.get("net_operating_income")
    ebitda_line = by_code.get("ebitda")

    total_revenue_actual = total_rev_line.actual if total_rev_line else 0
    total_revenue_budget = total_rev_line.budget if total_rev_line else 0
    gop_actual = gop_line.actual if gop_line else 0
    gop_budget = gop_line.budget if gop_line else 0
    noi_actual = noi_line.actual if noi_line else 0
    noi_budget = noi_line.budget if noi_line else 0
    # EBITDA: use explicit line if present, otherwise fall back to NOI
    ebitda_actual = ebitda_line.actual if ebitda_line else noi_actual
    ebitda_budget = ebitda_line.budget if ebitda_line else noi_budget

    gop_margin = (gop_actual / total_revenue_actual) if total_revenue_actual else 0.0
    gop_margin_budget = (gop_budget / total_revenue_budget) if total_revenue_budget else 0.0

    return APIResponse(
        data=PLKPIResponse(
            property_id=property_id,
            property_name=prop.name,
            start_date=start,
            end_date=end,
            occupancy=round(occupancy, 4),
            occupancy_budget=round(bgt_occupancy, 4),
            adr=adr,
            adr_budget=bgt_adr,
            revpar=revpar,
            revpar_budget=bgt_revpar,
            total_revenue=total_revenue_actual,
            total_revenue_budget=total_revenue_budget,
            gop=gop_actual,
            gop_budget=gop_budget,
            gop_margin=round(gop_margin, 4),
            gop_margin_budget=round(gop_margin_budget, 4),
            noi=noi_actual,
            noi_budget=noi_budget,
            ebitda=ebitda_actual,
            ebitda_budget=ebitda_budget,
        )
    )


@router.get(
    "/dept-detail/{property_id}/{dept_type}",
    response_model=APIResponse[DeptDetailResponse],
)
async def dept_detail(
    dept_type: str = Path(..., regex="^(rooms|fb|golf|mountain|spa|retail)$"),
    property_id: uuid.UUID = Depends(require_property_access),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis),
):
    import calendar as _cal

    from sqlalchemy import text as sa_text

    import logging, traceback
    try:
        return await _dept_detail_inner(dept_type, property_id, start, end, current_user, db, redis_client)
    except HTTPException:
        raise
    except Exception as e:
        logging.getLogger(__name__).error("dept_detail error: %s\n%s", e, traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

async def _dept_detail_inner(dept_type, property_id, start, end, current_user, db, redis_client):
    import calendar as _cal
    from sqlalchemy import text as sa_text

    dept_cfg = _DEPT_TYPE_MAP.get(dept_type)
    if not dept_cfg:
        raise HTTPException(status_code=400, detail=f"Unknown department type: {dept_type}")

    prop = await property_service.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    # Default to MTD if no dates provided
    today = date.today()
    eff_start = start or today.replace(day=1)
    eff_end = end or today
    period = "custom" if (start and end) else "mtd"

    cache = CacheService(redis_client)

    # Reuse the full inter-month report to get hierarchical P&L lines
    report = await report_service.get_inter_month(
        db=db,
        property_id=property_id,
        property_name=prop.name,
        period=period,
        start_date=eff_start,
        end_date=eff_end,
        cache=cache,
        tenant_id=current_user.tenant_id,
    )

    # Filter P&L lines to this department
    dept_keywords = {
        "rooms": ["room"],
        "fb": ["food", "f&b", "beverage", "catering"],
        "golf": ["golf"],
        "mountain": ["mountain"],
        "spa": ["spa"],
        "retail": ["retail"],
    }
    keywords = dept_keywords.get(dept_type, [dept_type])

    # Top-level lines are Total Revenue, Total Dept Expenses, etc.
    # Need to fetch their children to find department-level lines (Rooms Revenue, Rooms Expense, etc.)
    all_children = []
    for top_line in report.lines:
        if top_line.is_summary and top_line.depth == 0:
            try:
                kids = await report_service.get_children(
                    db=db,
                    property_id=property_id,
                    parent_id=top_line.id,
                    period=period,
                    start_date=eff_start,
                    end_date=eff_end,
                    cache=cache,
                    tenant_id=current_user.tenant_id,
                )
                all_children.extend(kids)
            except Exception:
                pass

    # Find department root among children (e.g. "Rooms Revenue", "Rooms Expense")
    dept_roots = []
    for child in all_children:
        if any(kw in child.name.lower() for kw in keywords):
            dept_roots.append(child)

    pl_lines: list[DeptPLLine] = []
    for root_line in dept_roots:
        pl_lines.append(DeptPLLine(
            id=root_line.id,
            code=root_line.code,
            name=root_line.name,
            parent_id=root_line.parent_id,
            is_summary=root_line.is_summary,
            data_type=root_line.data_type,
            sort_order=root_line.sort_order,
            depth=0,
            actual=root_line.actual,
            budget=root_line.budget,
            variance_dollars=root_line.variance_dollars,
            variance_pct=root_line.variance_pct,
            forecast_lock=root_line.forecast_lock,
            prior_year_actual=root_line.prior_year_actual,
            py_variance_dollars=root_line.py_variance_dollars,
            py_variance_pct=root_line.py_variance_pct,
        ))

        # Fetch grandchildren (line item detail under each dept root)
        try:
            grandkids = await report_service.get_children(
                db=db,
                property_id=property_id,
                parent_id=root_line.id,
                period=period,
                start_date=eff_start,
                end_date=eff_end,
                cache=cache,
                tenant_id=current_user.tenant_id,
            )
            for child in grandkids:
                if child.id not in {pl.id for pl in pl_lines}:
                    pl_lines.append(DeptPLLine(
                        id=child.id,
                        code=child.code,
                        name=child.name,
                        parent_id=child.parent_id,
                        is_summary=child.is_summary,
                        data_type=child.data_type,
                        sort_order=child.sort_order,
                        depth=1,
                        actual=child.actual,
                        budget=child.budget,
                        variance_dollars=child.variance_dollars,
                        variance_pct=child.variance_pct,
                        forecast_lock=child.forecast_lock,
                        prior_year_actual=child.prior_year_actual,
                        py_variance_dollars=child.py_variance_dollars,
                        py_variance_pct=child.py_variance_pct,
                    ))
        except Exception:
            pass

    pl_lines.sort(key=lambda x: x.sort_order)

    # Build department-specific KPIs
    days_in_range = (eff_end - eff_start).days + 1

    all_codes = list(set(
        dept_cfg["revenue_codes"]
        + dept_cfg["expense_codes"]
        + [dept_cfg.get(k, "") for k in [
            "count_code", "available_code", "labor_code",
            "food_cost_code", "bev_cost_code", "covers_code", "rooms_sold_code",
            "cart_code", "pro_shop_code",
            "lift_code", "rental_code", "lessons_code", "snowmaking_code",
            "services_code", "retail_code", "capacity_code", "cogs_code",
        ] if dept_cfg.get(k)]
    ))

    result = await db.execute(
        sa_text("""
            SELECT li.code, SUM(da.value) AS total
            FROM daily_actuals da
            JOIN line_items li ON li.id = da.line_item_id
            WHERE da.property_id = :property_id
              AND da.date >= :start_date AND da.date <= :end_date
              AND li.code = ANY(:codes)
            GROUP BY li.code
        """),
        {"property_id": property_id, "start_date": eff_start, "end_date": eff_end, "codes": all_codes},
    )
    actuals = {row.code: row.total for row in result.fetchall()}

    # Budget values (prorated)
    budget_result = await db.execute(
        sa_text("""
            SELECT li.code, b.year, b.month, b.value
            FROM budgets b
            JOIN line_items li ON li.id = b.line_item_id
            WHERE b.property_id = :property_id
              AND (b.year * 100 + b.month) >= :start_ym
              AND (b.year * 100 + b.month) <= :end_ym
              AND li.code = ANY(:codes)
        """),
        {
            "property_id": property_id,
            "start_ym": eff_start.year * 100 + eff_start.month,
            "end_ym": eff_end.year * 100 + eff_end.month,
            "codes": all_codes,
        },
    )
    budgets: dict[str, float] = {}
    for row in budget_result.fetchall():
        dim = _cal.monthrange(row.year, row.month)[1]
        m_start = date(row.year, row.month, 1)
        m_end = date(row.year, row.month, dim)
        r_start = max(m_start, eff_start)
        r_end = min(m_end, eff_end)
        days = (r_end - r_start).days + 1
        prorated = row.value * days / dim
        budgets[row.code] = budgets.get(row.code, 0) + prorated

    def _a(code: str) -> float:
        return float(actuals.get(code, 0))

    def _b(code: str) -> float:
        return float(budgets.get(code, 0))

    def _sum_a(codes: list[str]) -> float:
        return sum(_a(c) for c in codes)

    def _sum_b(codes: list[str]) -> float:
        return sum(_b(c) for c in codes)

    kpis: list[DeptKPI] = []

    if dept_type == "rooms":
        rooms_sold = _a("rooms_sold")
        bgt_rooms_sold = _b("rooms_sold")
        avail = (prop.available_rooms or 0) * days_in_range
        bgt_avail = avail
        room_rev = _sum_a(dept_cfg["revenue_codes"])
        bgt_room_rev = _sum_b(dept_cfg["revenue_codes"])
        labor = _a("rooms_labor")
        bgt_labor = _b("rooms_labor")

        occ = rooms_sold / avail if avail else 0.0
        bgt_occ = bgt_rooms_sold / bgt_avail if bgt_avail else 0.0
        adr = room_rev / rooms_sold if rooms_sold else 0.0
        bgt_adr = bgt_room_rev / bgt_rooms_sold if bgt_rooms_sold else 0.0
        revpar = room_rev / avail if avail else 0.0
        bgt_revpar = bgt_room_rev / bgt_avail if bgt_avail else 0.0
        cpor = labor / rooms_sold if rooms_sold else 0.0
        bgt_cpor = bgt_labor / bgt_rooms_sold if bgt_rooms_sold else 0.0

        kpis = [
            DeptKPI(label="Occupancy %", actual=round(occ, 4), budget=round(bgt_occ, 4), variance=round(occ - bgt_occ, 4), unit="percentage"),
            DeptKPI(label="ADR", actual=round(adr), budget=round(bgt_adr), variance=round(adr - bgt_adr), unit="currency"),
            DeptKPI(label="RevPAR", actual=round(revpar), budget=round(bgt_revpar), variance=round(revpar - bgt_revpar), unit="currency"),
            DeptKPI(label="Rooms Sold", actual=rooms_sold, budget=bgt_rooms_sold, variance=rooms_sold - bgt_rooms_sold, unit="integer"),
            DeptKPI(label="Available Rooms", actual=avail, budget=bgt_avail, variance=0, unit="integer"),
            DeptKPI(label="Labor CPOR", actual=round(cpor), budget=round(bgt_cpor), variance=round(cpor - bgt_cpor), unit="currency"),
        ]

    elif dept_type == "fb":
        rev = _sum_a(dept_cfg["revenue_codes"])
        bgt_rev = _sum_b(dept_cfg["revenue_codes"])
        food_cost = _a("fb_cost_of_sales")
        bgt_food_cost = _b("fb_cost_of_sales")
        labor = _a("fb_labor")
        bgt_labor = _b("fb_labor")
        covers = _a("fb_covers")
        bgt_covers = _b("fb_covers")
        rooms_sold = _a("rooms_sold")

        food_pct = food_cost / rev if rev else 0.0
        bgt_food_pct = bgt_food_cost / bgt_rev if bgt_rev else 0.0
        labor_pct = labor / rev if rev else 0.0
        bgt_labor_pct = bgt_labor / bgt_rev if bgt_rev else 0.0
        avg_check = rev / covers if covers else 0.0
        bgt_avg_check = bgt_rev / bgt_covers if bgt_covers else 0.0
        fb_por = rev / rooms_sold if rooms_sold else 0.0

        kpis = [
            DeptKPI(label="Total F&B Revenue", actual=round(rev), budget=round(bgt_rev), variance=round(rev - bgt_rev), unit="currency"),
            DeptKPI(label="Food Cost %", actual=round(food_pct, 4), budget=round(bgt_food_pct, 4), variance=round(food_pct - bgt_food_pct, 4), unit="percentage"),
            DeptKPI(label="Labor %", actual=round(labor_pct, 4), budget=round(bgt_labor_pct, 4), variance=round(labor_pct - bgt_labor_pct, 4), unit="percentage"),
            DeptKPI(label="Covers", actual=covers, budget=bgt_covers, variance=covers - bgt_covers, unit="integer"),
            DeptKPI(label="Avg Check", actual=round(avg_check), budget=round(bgt_avg_check), variance=round(avg_check - bgt_avg_check), unit="currency"),
            DeptKPI(label="F&B Per Occupied Room", actual=round(fb_por), budget=0, variance=round(fb_por), unit="currency"),
        ]

    elif dept_type == "golf":
        rev = _sum_a(dept_cfg["revenue_codes"])
        bgt_rev = _sum_b(dept_cfg["revenue_codes"])
        rounds_played = _a("golf_rounds")
        bgt_rounds = _b("golf_rounds")
        cart_rev = _a("golf_cart_revenue")
        bgt_cart = _b("golf_cart_revenue")
        pro_shop = _a("golf_pro_shop_revenue")
        bgt_pro_shop = _b("golf_pro_shop_revenue")
        labor = _a("golf_labor")
        bgt_labor = _b("golf_labor")
        labor_pct = labor / rev if rev else 0.0
        bgt_labor_pct = bgt_labor / bgt_rev if bgt_rev else 0.0
        rev_per_round = rev / rounds_played if rounds_played else 0.0
        bgt_rpr = bgt_rev / bgt_rounds if bgt_rounds else 0.0

        kpis = [
            DeptKPI(label="Rounds Played", actual=rounds_played, budget=bgt_rounds, variance=rounds_played - bgt_rounds, unit="integer"),
            DeptKPI(label="Rev/Round", actual=round(rev_per_round), budget=round(bgt_rpr), variance=round(rev_per_round - bgt_rpr), unit="currency"),
            DeptKPI(label="Cart Revenue", actual=round(cart_rev), budget=round(bgt_cart), variance=round(cart_rev - bgt_cart), unit="currency"),
            DeptKPI(label="Pro Shop Revenue", actual=round(pro_shop), budget=round(bgt_pro_shop), variance=round(pro_shop - bgt_pro_shop), unit="currency"),
            DeptKPI(label="Labor %", actual=round(labor_pct, 4), budget=round(bgt_labor_pct, 4), variance=round(labor_pct - bgt_labor_pct, 4), unit="percentage"),
        ]

    elif dept_type == "mountain":
        rev = _sum_a(dept_cfg["revenue_codes"])
        bgt_rev = _sum_b(dept_cfg["revenue_codes"])
        visits = _a("mountain_skier_visits")
        bgt_visits = _b("mountain_skier_visits")
        rev_per_visit = rev / visits if visits else 0.0
        bgt_rpv = bgt_rev / bgt_visits if bgt_visits else 0.0
        lift = _a("mountain_lift_revenue")
        bgt_lift = _b("mountain_lift_revenue")
        rental = _a("mountain_rental_revenue")
        bgt_rental = _b("mountain_rental_revenue")
        lessons = _a("mountain_lessons_revenue")
        bgt_lessons = _b("mountain_lessons_revenue")
        snowmaking = _a("mountain_snowmaking")
        bgt_snowmaking = _b("mountain_snowmaking")

        kpis = [
            DeptKPI(label="Skier Visits", actual=visits, budget=bgt_visits, variance=visits - bgt_visits, unit="integer"),
            DeptKPI(label="Rev/Visit", actual=round(rev_per_visit), budget=round(bgt_rpv), variance=round(rev_per_visit - bgt_rpv), unit="currency"),
            DeptKPI(label="Lift Revenue", actual=round(lift), budget=round(bgt_lift), variance=round(lift - bgt_lift), unit="currency"),
            DeptKPI(label="Rental Revenue", actual=round(rental), budget=round(bgt_rental), variance=round(rental - bgt_rental), unit="currency"),
            DeptKPI(label="Lessons Revenue", actual=round(lessons), budget=round(bgt_lessons), variance=round(lessons - bgt_lessons), unit="currency"),
            DeptKPI(label="Snowmaking Cost", actual=round(snowmaking), budget=round(bgt_snowmaking), variance=round(snowmaking - bgt_snowmaking), unit="currency"),
        ]

    elif dept_type == "spa":
        rev = _sum_a(dept_cfg["revenue_codes"])
        bgt_rev = _sum_b(dept_cfg["revenue_codes"])
        treatments = _a("spa_treatments")
        bgt_treatments = _b("spa_treatments")
        rev_per_t = rev / treatments if treatments else 0.0
        bgt_rpt = bgt_rev / bgt_treatments if bgt_treatments else 0.0
        services = _a("spa_services_revenue")
        bgt_services = _b("spa_services_revenue")
        retail = _a("spa_retail_revenue")
        bgt_retail = _b("spa_retail_revenue")
        capacity = _a("spa_capacity")
        util = treatments / capacity if capacity else 0.0
        bgt_util = bgt_treatments / _b("spa_capacity") if _b("spa_capacity") else 0.0
        labor = _a("spa_labor")
        bgt_labor = _b("spa_labor")
        labor_pct = labor / rev if rev else 0.0
        bgt_labor_pct = bgt_labor / bgt_rev if bgt_rev else 0.0

        kpis = [
            DeptKPI(label="Treatments", actual=treatments, budget=bgt_treatments, variance=treatments - bgt_treatments, unit="integer"),
            DeptKPI(label="Rev/Treatment", actual=round(rev_per_t), budget=round(bgt_rpt), variance=round(rev_per_t - bgt_rpt), unit="currency"),
            DeptKPI(label="Services Revenue", actual=round(services), budget=round(bgt_services), variance=round(services - bgt_services), unit="currency"),
            DeptKPI(label="Retail Revenue", actual=round(retail), budget=round(bgt_retail), variance=round(retail - bgt_retail), unit="currency"),
            DeptKPI(label="Utilization %", actual=round(util, 4), budget=round(bgt_util, 4), variance=round(util - bgt_util, 4), unit="percentage"),
            DeptKPI(label="Labor %", actual=round(labor_pct, 4), budget=round(bgt_labor_pct, 4), variance=round(labor_pct - bgt_labor_pct, 4), unit="percentage"),
        ]

    elif dept_type == "retail":
        rev = _sum_a(dept_cfg["revenue_codes"])
        bgt_rev = _sum_b(dept_cfg["revenue_codes"])
        cogs = _a("retail_cost_of_sales")
        bgt_cogs = _b("retail_cost_of_sales")
        labor = _a("retail_labor")
        bgt_labor = _b("retail_labor")
        margin = (rev - cogs) / rev if rev else 0.0
        bgt_margin = (bgt_rev - bgt_cogs) / bgt_rev if bgt_rev else 0.0
        cogs_pct = cogs / rev if rev else 0.0
        bgt_cogs_pct = bgt_cogs / bgt_rev if bgt_rev else 0.0
        labor_pct = labor / rev if rev else 0.0
        bgt_labor_pct = bgt_labor / bgt_rev if bgt_rev else 0.0

        kpis = [
            DeptKPI(label="Revenue", actual=round(rev), budget=round(bgt_rev), variance=round(rev - bgt_rev), unit="currency"),
            DeptKPI(label="Margin %", actual=round(margin, 4), budget=round(bgt_margin, 4), variance=round(margin - bgt_margin, 4), unit="percentage"),
            DeptKPI(label="COGS %", actual=round(cogs_pct, 4), budget=round(bgt_cogs_pct, 4), variance=round(cogs_pct - bgt_cogs_pct, 4), unit="percentage"),
            DeptKPI(label="Labor %", actual=round(labor_pct, 4), budget=round(bgt_labor_pct, 4), variance=round(labor_pct - bgt_labor_pct, 4), unit="percentage"),
        ]

    return APIResponse(
        data=DeptDetailResponse(
            property_id=property_id,
            property_name=prop.name,
            dept_name=dept_cfg["name"],
            dept_type=dept_type,
            period=period,
            start_date=eff_start,
            end_date=eff_end,
            kpis=kpis,
            pl_lines=pl_lines,
        )
    )


class MonthCloseItem(BaseModel):
    year: int
    month: int
    is_closed: bool
    closed_at: str | None


@router.get(
    "/month-close/{property_id}",
    response_model=APIResponse[list[MonthCloseItem]],
)
async def month_close_status(
    property_id: uuid.UUID = Depends(require_property_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(MonthCloseStatus)
        .where(MonthCloseStatus.property_id == property_id)
        .order_by(MonthCloseStatus.year, MonthCloseStatus.month)
    )
    rows = result.scalars().all()
    items = [
        MonthCloseItem(
            year=r.year,
            month=r.month,
            is_closed=r.is_closed,
            closed_at=r.closed_at.isoformat() if r.closed_at else None,
        )
        for r in rows
    ]
    return APIResponse(data=items)
