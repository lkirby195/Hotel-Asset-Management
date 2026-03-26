import uuid
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.commentary import Commentary


class CommentaryService:
    async def create(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        property_id: uuid.UUID,
        user_id: uuid.UUID,
        year: int,
        month: int,
        category_tag: str,
        text: str,
        department_tag: Optional[str] = None,
    ) -> Commentary:
        comment = Commentary(
            tenant_id=tenant_id,
            property_id=property_id,
            user_id=user_id,
            year=year,
            month=month,
            category_tag=category_tag,
            text=text,
            department_tag=department_tag,
        )
        db.add(comment)
        await db.flush()
        await db.refresh(comment, attribute_names=['user'])
        return comment

    async def list_by_property_month(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        year: int,
        month: int,
    ) -> list[Commentary]:
        stmt = (
            select(Commentary)
            .where(
                Commentary.property_id == property_id,
                Commentary.year == year,
                Commentary.month == month,
            )
            .order_by(Commentary.created_at.desc())
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        db: AsyncSession,
        comment_id: uuid.UUID,
        user_id: uuid.UUID,
        text: str,
    ) -> Optional[Commentary]:
        result = await db.execute(
            select(Commentary).where(
                Commentary.id == comment_id,
                Commentary.user_id == user_id,
            )
        )
        comment = result.scalar_one_or_none()
        if not comment:
            return None
        comment.text = text
        await db.flush()
        await db.refresh(comment, attribute_names=['user'])
        return comment

    async def delete(self, db: AsyncSession, comment_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        """Delete a comment. Only the author can delete their own comments."""
        result = await db.execute(
            delete(Commentary).where(
                Commentary.id == comment_id,
                Commentary.user_id == user_id,
            )
        )
        return result.rowcount > 0

    async def get_by_id(self, db: AsyncSession, comment_id: uuid.UUID) -> Optional[Commentary]:
        result = await db.execute(select(Commentary).where(Commentary.id == comment_id))
        return result.scalar_one_or_none()
