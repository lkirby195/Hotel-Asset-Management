import uuid

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.property import Property
from app.models.user import User, user_properties


class UserService:

    async def list_users(self, db: AsyncSession) -> list[User]:
        result = await db.execute(
            select(User)
            .options(selectinload(User.properties))
            .order_by(User.name)
        )
        return list(result.scalars().all())

    async def get_user(self, db: AsyncSession, user_id: uuid.UUID) -> User | None:
        result = await db.execute(
            select(User)
            .options(selectinload(User.properties))
            .where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_user(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        clerk_id: str,
        email: str,
        name: str,
        role: str,
        property_ids: list[uuid.UUID],
    ) -> User:
        user = User(
            tenant_id=tenant_id,
            clerk_id=clerk_id,
            email=email,
            name=name,
            role=role,
        )
        db.add(user)
        await db.flush()

        if property_ids:
            await self._assign_properties(db, user, tenant_id, property_ids)

        return user

    async def update_user(
        self,
        db: AsyncSession,
        user: User,
        email: str | None = None,
        name: str | None = None,
        role: str | None = None,
        is_active: bool | None = None,
        property_ids: list[uuid.UUID] | None = None,
    ) -> User:
        if email is not None:
            user.email = email
        if name is not None:
            user.name = name
        if role is not None:
            user.role = role
        if is_active is not None:
            user.is_active = is_active

        if property_ids is not None:
            # Clear existing assignments and reassign
            await db.execute(
                delete(user_properties).where(user_properties.c.user_id == user.id)
            )
            await self._assign_properties(db, user, user.tenant_id, property_ids)

        await db.flush()
        return user

    async def delete_user(self, db: AsyncSession, user: User) -> None:
        await db.delete(user)

    async def _assign_properties(
        self,
        db: AsyncSession,
        user: User,
        tenant_id: uuid.UUID,
        property_ids: list[uuid.UUID],
    ) -> None:
        for pid in property_ids:
            await db.execute(
                user_properties.insert().values(
                    user_id=user.id,
                    property_id=pid,
                    tenant_id=tenant_id,
                )
            )
