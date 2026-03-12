import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session, require_role
from app.models.user import User
from app.schemas.common import APIResponse
from app.schemas.user import UserCreateRequest, UserSchema, UserUpdateRequest
from app.services.user_service import UserService

router = APIRouter()
user_service = UserService()


@router.post("/sync")
async def trigger_sync(
    current_user: User = Depends(require_role("admin")),
):
    """Trigger ProfitSword data sync. Returns a task ID for polling status."""
    from app.tasks.sync_pipeline import run_sync_pipeline

    task = run_sync_pipeline.delay(str(current_user.tenant_id))
    return APIResponse(data={"task_id": task.id, "status": "started"})


@router.get("/sync/{task_id}")
async def sync_status(
    task_id: str,
    current_user: User = Depends(require_role("admin")),
):
    """Check the status of a sync task."""
    from celery.result import AsyncResult
    from app.tasks.celery_app import celery_app

    result = AsyncResult(task_id, app=celery_app)
    return APIResponse(data={
        "task_id": task_id,
        "status": result.status,
        "result": str(result.result) if result.result else None,
    })


# --- User Management ---

@router.get("/users", response_model=APIResponse[list[UserSchema]])
async def list_users(
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db_session),
):
    users = await user_service.list_users(db)
    return APIResponse(data=[UserSchema.from_user(u) for u in users])


@router.post("/users", response_model=APIResponse[UserSchema], status_code=201)
async def create_user(
    body: UserCreateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db_session),
):
    user = await user_service.create_user(
        db=db,
        tenant_id=current_user.tenant_id,
        clerk_id=body.clerk_id,
        email=body.email,
        name=body.name,
        role=body.role,
        property_ids=body.property_ids,
    )
    return APIResponse(data=UserSchema.from_user(user))


@router.put("/users/{user_id}", response_model=APIResponse[UserSchema])
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateRequest,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db_session),
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    updated = await user_service.update_user(
        db=db,
        user=user,
        email=body.email,
        name=body.name,
        role=body.role,
        is_active=body.is_active,
        property_ids=body.property_ids,
    )
    return APIResponse(data=UserSchema.from_user(updated))


@router.delete("/users/{user_id}", status_code=204)
async def delete_user(
    user_id: uuid.UUID,
    current_user: User = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db_session),
):
    user = await user_service.get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    await user_service.delete_user(db, user)


# --- ProfitSword Discovery ---

@router.get("/profitsword/datasets")
async def list_datasets(
    current_user: User = Depends(require_role("admin")),
):
    """Fetch available ProfitSword dataset IDs. Use these to configure .env."""
    from app.tasks.sync_actuals import _get_adapter
    adapter = _get_adapter()
    try:
        datasets = await adapter.fetch_datasets()
        return APIResponse(data=[
            {"dataset_id": ds.dataset_id, "description": ds.description}
            for ds in datasets
        ])
    finally:
        if hasattr(adapter, "close"):
            await adapter.close()


@router.get("/profitsword/sites")
async def list_sites(
    current_user: User = Depends(require_role("admin")),
):
    """Fetch available ProfitSword sites/properties."""
    from app.tasks.sync_actuals import _get_adapter
    adapter = _get_adapter()
    try:
        sites = await adapter.fetch_sites()
        return APIResponse(data=[
            {
                "site_tag": s.site_tag,
                "site_name": s.site_name,
                "city": s.city,
                "state": s.state,
            }
            for s in sites
        ])
    finally:
        if hasattr(adapter, "close"):
            await adapter.close()
