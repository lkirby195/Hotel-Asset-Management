import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.property import Property
from app.models.user import User, user_properties


class PropertyService:

    async def get_user_properties(self, db: AsyncSession, user: User) -> list[Property]:
        if user.role in ("executive", "admin"):
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
                    user_properties.c.user_id == user.id,
                    Property.is_active == True,  # noqa: E712
                )
                .order_by(Property.name)
            )
        return list(result.scalars().all())

    async def get_property(self, db: AsyncSession, property_id: uuid.UUID) -> Property | None:
        result = await db.execute(
            select(Property)
            .options(selectinload(Property.departments))
            .where(Property.id == property_id)
        )
        return result.scalar_one_or_none()
