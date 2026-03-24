import uuid
from datetime import date

from pydantic import BaseModel


class DualPanelRow(BaseModel):
    line_name: str
    daily_actual: int | float | None = None
    daily_forecast: int | float | None = None
    daily_stly: int | float | None = None
    daily_vs_forecast: int | float | None = None
    daily_vs_stly: int | float | None = None
    mtd_actual: int | float | None = None
    mtd_budget: int | float | None = None
    mtd_stly: int | float | None = None
    mtd_fcst_lock: int | float | None = None
    mtd_vs_budget: int | float | None = None
    mtd_vs_stly: int | float | None = None
    is_header: bool = False
    is_total: bool = False
    indent: int = 0  # 0-2
    unit: str = "currency"  # 'currency', 'percentage', 'integer', 'decimal'


class DailyReportSection(BaseModel):
    section_name: str
    rows: list[DualPanelRow]


class DailyReportResponse(BaseModel):
    property_id: uuid.UUID
    property_name: str
    report_date: date
    available_rooms: int
    sections: dict[str, list[DailyReportSection]]
