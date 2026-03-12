import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user, get_db_session, require_property_access
from app.models.property import Property
from app.models.user import User, user_properties
from app.schemas.common import APIResponse
from app.schemas.property import PropertySchema

router = APIRouter()


@router.get("", response_model=APIResponse[list[PropertySchema]])
async def list_properties(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    if current_user.role in ("executive", "admin"):
        result = await db.execute(
            select(Property)
            .options(selectinload(Property.departments))
            .where(Property.is_active == True)  # noqa: E712
            .order_by(Property.name)
        )
    else:
        result = await db.execute(
            select(Property)
            .options(selectinload(Property.departments))
            .join(user_properties, Property.id == user_properties.c.property_id)
            .where(
                user_properties.c.user_id == current_user.id,
                Property.is_active == True,  # noqa: E712
            )
            .order_by(Property.name)
        )

    properties = result.scalars().all()
    return APIResponse(data=[PropertySchema.model_validate(p) for p in properties])


@router.get("/{property_id}", response_model=APIResponse[PropertySchema])
async def get_property(
    property_id: uuid.UUID = Depends(require_property_access),
    db: AsyncSession = Depends(get_db_session),
):
    result = await db.execute(
        select(Property)
        .options(selectinload(Property.departments))
        .where(Property.id == property_id)
    )
    prop = result.scalar_one_or_none()
    if not prop:
        raise HTTPException(status_code=404, detail="Property not found")
    return APIResponse(data=PropertySchema.model_validate(prop))
