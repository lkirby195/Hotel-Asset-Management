import uuid
from datetime import date

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_client import get_redis
from app.dependencies import get_current_user, get_db_session, require_property_access
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.report import InterMonthResponse, ReportLineItem
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
    period: str = Query(default="mtd", pattern="^(mtd|qtd|ytd|t28|custom|weekly)$"),
    start: date | None = Query(default=None),
    end: date | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
    redis_client: redis.Redis = Depends(get_redis),
):
    if period == "custom" and (not start or not end):
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
    period: str = Query(default="mtd", pattern="^(mtd|qtd|ytd|t28|custom|weekly)$"),
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
