import uuid
from datetime import date

from pydantic import BaseModel


class YesterdayKPI(BaseModel):
    metric_name: str
    actual: float
    budget: float
    stly: float
    variance_budget: float
    variance_budget_pct: float | None
    variance_stly: float
    variance_stly_pct: float | None
    unit: str  # 'currency', 'percentage', 'integer'


class YesterdayResponse(BaseModel):
    property_id: uuid.UUID
    property_name: str
    date: date
    kpis: list[YesterdayKPI]
