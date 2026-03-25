import uuid
from datetime import date

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import get_redis
from app.dependencies import get_current_user, get_db_session, require_property_access
from app.models.month_close import MonthCloseStatus
from app.models.user import User
from app.schemas.common import APIResponse, TimePeriod
from app.schemas.report import InterMonthResponse, PLKPIResponse, ReportLineItem
from app.services.cache_service import CacheService
from app.services.property_service import PropertyService
from app.services.report_service import ReportService

router = APIRouter()
report_service = ReportService()
property_service = PropertyService()


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
    ebitda_actual = ebitda_line.actual if ebitda_line else 0
    ebitda_budget = ebitda_line.budget if ebitda_line else 0

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
