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
    forecast_lock: int | None = None
    prior_year_actual: int | None
    py_variance_dollars: int | None
    py_variance_pct: float | None


class PLKPIResponse(BaseModel):
    property_id: uuid.UUID
    property_name: str
    start_date: date
    end_date: date
    occupancy: float
    occupancy_budget: float
    adr: int  # cents
    adr_budget: int
    revpar: int  # cents
    revpar_budget: int
    total_revenue: int  # cents
    total_revenue_budget: int
    gop: int  # cents
    gop_budget: int
    gop_margin: float
    gop_margin_budget: float
    noi: int  # cents
    noi_budget: int
    ebitda: int  # cents
    ebitda_budget: int


class PerformanceStatItem(BaseModel):
    label: str
    value: float
    format: str  # "integer", "currency", "percentage"


class InterMonthResponse(BaseModel):
    property_id: uuid.UUID
    property_name: str
    period: str
    start_date: date
    end_date: date
    lines: list[ReportLineItem]
    performance: list[PerformanceStatItem] = []
    note: str | None = None
