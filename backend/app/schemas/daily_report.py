import uuid
from datetime import date

from pydantic import BaseModel


class DualPanelRow(BaseModel):
    line_name: str
    daily_actual: float | None = None
    daily_forecast: float | None = None
    daily_stly: float | None = None
    daily_vs_forecast: float | None = None
    daily_vs_stly: float | None = None
    mtd_actual: float | None = None
    mtd_budget: float | None = None
    mtd_stly: float | None = None
    mtd_fcst_lock: float | None = None
    mtd_vs_budget: float | None = None
    mtd_vs_stly: float | None = None
    is_header: bool = False
    is_total: bool = False
    indent: int = 0
    unit: str = "currency"


class DailyReportSection(BaseModel):
    section_name: str
    rows: list[DualPanelRow]


class DailyReportResponse(BaseModel):
    property_id: uuid.UUID
    property_name: str
    report_date: date
    available_rooms: int
    sections: dict[str, list[DailyReportSection]]
