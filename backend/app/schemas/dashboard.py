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


class MTDPaceRow(BaseModel):
    metric_name: str
    actual: float
    budget: float
    stly: float
    forecast_lock: float
    vs_budget: float
    vs_budget_pct: float | None
    vs_stly: float
    vs_stly_pct: float | None
    vs_forecast: float
    unit: str  # 'currency', 'percentage', 'integer'


class MTDPaceResponse(BaseModel):
    property_id: uuid.UUID
    property_name: str
    period_start: date
    period_end: date
    days_elapsed: int
    days_in_month: int
    rows: list[MTDPaceRow]


# ── Forward Look / OTB ─────────────────────────────────────────


class OTBSummaryCard(BaseModel):
    window_name: str  # e.g. 'Rest of Month', 'Next 14 Days', 'Next 30 Days'
    date_start: date
    date_end: date
    nights: int
    otb_revenue: int  # cents
    otb_occupancy: float
    otb_adr: int  # cents
    stly_revenue: int  # cents
    vs_stly_revenue: int  # cents
    vs_stly_pct: float | None
    budget_remaining: int | None  # cents
    pickup_7day: int | None  # cents — revenue pickup in last 7 days


class OTBDailyRow(BaseModel):
    date: date
    day_of_week: str
    transient_rooms: int
    group_rooms: int
    total_rooms: int
    occupancy: float
    adr: int  # cents
    revenue: int  # cents
    stly_rooms: int
    stly_revenue: int  # cents
    vs_stly_pct: float | None


class ForwardLookResponse(BaseModel):
    property_id: uuid.UUID
    property_name: str
    as_of_date: date
    available_rooms_per_night: int
    summary_cards: list[OTBSummaryCard]
    daily_detail: list[OTBDailyRow]
