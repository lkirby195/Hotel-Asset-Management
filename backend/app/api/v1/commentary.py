import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_current_user, get_db_session, require_property_access
from app.models.user import User
from app.schemas.commentary import CommentaryCreate, CommentaryResponse, CommentaryUpdate
from app.schemas.common import APIResponse
from app.services.commentary_service import CommentaryService

router = APIRouter()
commentary_service = CommentaryService()


def _to_response(c) -> CommentaryResponse:
    return CommentaryResponse(
        id=c.id,
        tenant_id=c.tenant_id,
        property_id=c.property_id,
        user_id=c.user_id,
        user_name=c.user.name if c.user else "Unknown",
        year=c.year,
        month=c.month,
        department_tag=c.department_tag,
        category_tag=c.category_tag,
        text=c.text,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


@router.get(
    "/{property_id}",
    response_model=APIResponse[list[CommentaryResponse]],
)
async def list_commentary(
    property_id: uuid.UUID = Depends(require_property_access),
    year: int = Query(...),
    month: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    comments = await commentary_service.list_by_property_month(
        db=db,
        property_id=property_id,
        year=year,
        month=month,
    )
    return APIResponse(data=[_to_response(c) for c in comments])


@router.post(
    "/{property_id}",
    response_model=APIResponse[CommentaryResponse],
    status_code=201,
)
async def create_commentary(
    body: CommentaryCreate,
    property_id: uuid.UUID = Depends(require_property_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    comment = await commentary_service.create(
        db=db,
        tenant_id=current_user.tenant_id,
        property_id=property_id,
        user_id=current_user.id,
        year=body.year,
        month=body.month,
        category_tag=body.category_tag,
        text=body.text,
        department_tag=body.department_tag,
    )
    return APIResponse(data=_to_response(comment))


@router.put(
    "/{property_id}/{comment_id}",
    response_model=APIResponse[CommentaryResponse],
)
async def update_commentary(
    comment_id: uuid.UUID,
    body: CommentaryUpdate,
    property_id: uuid.UUID = Depends(require_property_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    existing = await commentary_service.get_by_id(db, comment_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Comment not found")
    if existing.property_id != property_id:
        raise HTTPException(status_code=403, detail="Comment does not belong to this property")

    updated = await commentary_service.update(db, comment_id, current_user.id, body.text)
    if not updated:
        raise HTTPException(
            status_code=403,
            detail="You are not the author of this comment",
        )
    return APIResponse(data=_to_response(updated))


@router.delete(
    "/{property_id}/{comment_id}",
    response_model=APIResponse[dict],
)
async def delete_commentary(
    comment_id: uuid.UUID,
    property_id: uuid.UUID = Depends(require_property_access),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db_session),
):
    existing = await commentary_service.get_by_id(db, comment_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Comment not found")
    if existing.property_id != property_id:
        raise HTTPException(status_code=403, detail="Comment does not belong to this property")

    deleted = await commentary_service.delete(db, comment_id, current_user.id)
    if not deleted:
        raise HTTPException(
            status_code=403,
            detail="You are not the author of this comment",
        )
    return APIResponse(data={"deleted": True})
