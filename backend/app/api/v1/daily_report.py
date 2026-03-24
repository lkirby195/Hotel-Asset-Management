import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session, require_property_access
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.daily_report import DailyReportResponse
from app.services.daily_report_service import DailyReportService
from app.services.property_service import PropertyService

router = APIRouter()
daily_report_service = DailyReportService()
property_service = PropertyService()


@router.get(
    "/{property_id}",
    response_model=APIResponse[DailyReportResponse],
)
async def get_daily_report(
    property_id: uuid.UUID = Depends(require_property_access),
    target_date: date | None = Query(default=None, alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    prop = await property_service.get_property(db, property_id)
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    if not prop.available_rooms:
        raise HTTPException(status_code=422, detail="Property has no available_rooms configured")

    result = await daily_report_service.get_daily_report(
        db=db,
        property_id=property_id,
        property_name=prop.name,
        available_rooms=prop.available_rooms,
        target_date=target_date,
    )
    return APIResponse(data=result)
