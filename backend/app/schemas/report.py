import uuid
from datetime import date

from pydantic import BaseModel


class ReportLineItem(BaseModel):
    id: uuid.UUID
    code: str
    name: str
    parent_id: uuid.UUID | None
    is_summary: bool
    data_type: str  # 'revenue' or 'expense'
    sort_order: int
    depth: int
    actual: int  # cents
    budget: int  # cents
    variance_dollars: int
    variance_pct: float | None
    forecast_lock: int | None
    prior_year_actual: int | None
    py_variance_dollars: int | None
    py_variance_pct: float | None


class InterMonthResponse(BaseModel):
    property_id: uuid.UUID
    property_name: str
    period: str
    start_date: date
    end_date: date
    lines: list[ReportLineItem]
