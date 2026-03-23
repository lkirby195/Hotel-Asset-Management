import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session, require_property_access
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.dashboard import MTDPaceResponse, YesterdayResponse
from app.services.dashboard_service import DashboardService
from app.services.property_service import PropertyService

router = APIRouter()
dashboard_service = DashboardService()
property_service = PropertyService()


@router.get(
    "/yesterday/{property_id}",
    response_model=APIResponse[YesterdayResponse],
)
async def yesterday_performance(
    property_id: uuid.UUID = Depends(require_property_access),
    target_date: date | None = Query(default=None, alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    prop = await property_service.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    result = await dashboard_service.get_yesterday(
        db=db,
        property_id=property_id,
        property_name=prop.name,
        target_date=target_date,
    )
    return APIResponse(data=result)


@router.get(
    "/mtd-pace/{property_id}",
    response_model=APIResponse[MTDPaceResponse],
)
async def mtd_pace(
    property_id: uuid.UUID = Depends(require_property_access),
    target_date: date | None = Query(default=None, alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    prop = await property_service.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    result = await dashboard_service.get_mtd_pace(
        db=db,
        property_id=property_id,
        property_name=prop.name,
        target_date=target_date,
    )
    return APIResponse(data=result)
