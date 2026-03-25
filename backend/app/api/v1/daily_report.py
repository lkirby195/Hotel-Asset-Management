import uuid
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session, require_property_access
from app.models.property import Property
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.daily_report import DailyReportResponse
from app.services.daily_report_service import DailyReportService

router = APIRouter()

_service = DailyReportService()


@router.get("/{property_id}", response_model=APIResponse[DailyReportResponse])
async def get_daily_report(
    property_id: uuid.UUID = Depends(require_property_access),
    report_date: date | None = Query(None, alias="date"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    target_date = report_date or (date.today() - timedelta(days=1))

    result = await db.execute(
        select(Property).where(Property.id == property_id)
    )
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")

    report = await _service.get_daily_report(
        db=db,
        property_id=property_id,
        property_name=prop.name,
        available_rooms=prop.available_rooms or 0,
        target_date=target_date,
    )
    return APIResponse(data=report)
