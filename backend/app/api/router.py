from fastapi import APIRouter

from app.api.v1 import auth, daily_report, dashboard, properties, reports, admin

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(daily_report.router, prefix="/daily-report", tags=["daily-report"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
