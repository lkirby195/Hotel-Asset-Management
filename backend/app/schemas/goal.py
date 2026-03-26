import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class GoalCreate(BaseModel):
    metric_code: str = Field(..., max_length=50)
    target_value: int  # cents for currency, basis points for percentages
    period_type: str = Field(..., pattern="^(monthly|annual)$")
    year: int
    month: Optional[int] = Field(None, ge=1, le=12)


class GoalUpdate(BaseModel):
    target_value: Optional[int] = None
    metric_code: Optional[str] = None
    period_type: Optional[str] = None
    year: Optional[int] = None
    month: Optional[int] = None


class GoalResponse(BaseModel):
    id: uuid.UUID
    tenant_id: uuid.UUID
    property_id: uuid.UUID
    user_id: uuid.UUID
    metric_code: str
    target_value: int
    period_type: str
    year: int
    month: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
