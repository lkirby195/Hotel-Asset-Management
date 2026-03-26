import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CommentaryCreate(BaseModel):
    year: int
    month: int = Field(..., ge=1, le=12)
    department_tag: Optional[str] = Field(None, max_length=100)
    category_tag: str = Field(..., max_length=50)
    text: str = Field(..., min_length=1)


class CommentaryResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    property_id: uuid.UUID
    user_id: uuid.UUID
    user_name: str
    year: int
    month: int
    department_tag: Optional[str]
    category_tag: str
    text: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
