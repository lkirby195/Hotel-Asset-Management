import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session, require_property_access
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.goal import GoalCreate, GoalResponse, GoalUpdate
from app.services.goal_service import GoalService

router = APIRouter()
goal_service = GoalService()


@router.get(
    "/{property_id}",
    response_model=APIResponse[list[GoalResponse]],
)
async def list_goals(
    property_id: uuid.UUID = Depends(require_property_access),
    year: int | None = Query(default=None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    goals = await goal_service.list_by_property(
        db=db,
        property_id=property_id,
        user_id=current_user.id,
        year=year,
    )
    return APIResponse(data=[GoalResponse.model_validate(g) for g in goals])


@router.post(
    "/{property_id}",
    response_model=APIResponse[GoalResponse],
    status_code=201,
)
async def create_goal(
    body: GoalCreate,
    property_id: uuid.UUID = Depends(require_property_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    goal = await goal_service.create(
        db=db,
        tenant_id=current_user.tenant_id,
        property_id=property_id,
        user_id=current_user.id,
        metric_code=body.metric_code,
        target_value=body.target_value,
        period_type=body.period_type,
        year=body.year,
        month=body.month,
    )
    return APIResponse(data=GoalResponse.model_validate(goal))


@router.put(
    "/{property_id}/{goal_id}",
    response_model=APIResponse[GoalResponse],
)
async def update_goal(
    goal_id: uuid.UUID,
    body: GoalUpdate,
    property_id: uuid.UUID = Depends(require_property_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    existing = await goal_service.get_by_id(db, goal_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Goal not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only edit your own goals")

    updated = await goal_service.update(
        db=db,
        goal_id=goal_id,
        **body.model_dump(exclude_none=True),
    )
    return APIResponse(data=GoalResponse.model_validate(updated))


@router.delete(
    "/{property_id}/{goal_id}",
    response_model=APIResponse[dict],
)
async def delete_goal(
    goal_id: uuid.UUID,
    property_id: uuid.UUID = Depends(require_property_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    existing = await goal_service.get_by_id(db, goal_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Goal not found")
    if existing.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="You can only delete your own goals")

    await goal_service.delete(db, goal_id)
    return APIResponse(data={"deleted": True})
