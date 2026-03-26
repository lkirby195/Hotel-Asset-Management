import uuid
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.goal import Goal


class GoalService:
    async def create(
        self,
        db: AsyncSession,
        tenant_id: uuid.UUID,
        property_id: uuid.UUID,
        user_id: uuid.UUID,
        metric_code: str,
        target_value: int,
        period_type: str,
        year: int,
        month: Optional[int] = None,
    ) -> Goal:
        goal = Goal(
            tenant_id=tenant_id,
            property_id=property_id,
            user_id=user_id,
            metric_code=metric_code,
            target_value=target_value,
            period_type=period_type,
            year=year,
            month=month,
        )
        db.add(goal)
        await db.flush()
        return goal

    async def update(
        self,
        db: AsyncSession,
        goal_id: uuid.UUID,
        **kwargs,
    ) -> Optional[Goal]:
        result = await db.execute(select(Goal).where(Goal.id == goal_id))
        goal = result.scalar_one_or_none()
        if not goal:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(goal, key):
                setattr(goal, key, value)
        await db.flush()
        return goal

    async def delete(self, db: AsyncSession, goal_id: uuid.UUID) -> bool:
        result = await db.execute(delete(Goal).where(Goal.id == goal_id))
        return result.rowcount > 0

    async def list_by_property(
        self,
        db: AsyncSession,
        property_id: uuid.UUID,
        user_id: Optional[uuid.UUID] = None,
        year: Optional[int] = None,
    ) -> list[Goal]:
        stmt = select(Goal).where(Goal.property_id == property_id)
        if user_id:
            stmt = stmt.where(Goal.user_id == user_id)
        if year:
            stmt = stmt.where(Goal.year == year)
        stmt = stmt.order_by(Goal.metric_code, Goal.period_type, Goal.month)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, db: AsyncSession, goal_id: uuid.UUID) -> Optional[Goal]:
        result = await db.execute(select(Goal).where(Goal.id == goal_id))
        return result.scalar_one_or_none()
