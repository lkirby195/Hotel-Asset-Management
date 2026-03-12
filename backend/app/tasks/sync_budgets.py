import logging
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.line_item import LineItem
from app.models.property import Property
from app.tasks.celery_app import celery_app
from app.tasks.sync_actuals import _get_adapter, _get_sync_engine

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, name="sync_budgets")
def sync_budgets(self, tenant_id: str):
    """Fetch budgets and forecasts for current year and upsert into DB."""
    import asyncio

    engine = _get_sync_engine()
    today = date.today()

    with Session(engine) as session:
        session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))

        properties = session.execute(
            select(Property.id, Property.code).where(Property.is_active == True)  # noqa: E712
        ).fetchall()
        property_map = {p.code: p.id for p in properties}

        line_items = session.execute(select(LineItem.id, LineItem.code)).fetchall()
        line_item_map = {li.code: li.id for li in line_items}

        adapter = _get_adapter()

        # Fetch budgets
        budget_records = asyncio.get_event_loop().run_until_complete(
            adapter.fetch_budgets(list(property_map.keys()), today.year)
        )
        budget_count = 0
        for record in budget_records:
            prop_id = property_map.get(record.property_code)
            li_id = line_item_map.get(record.account_code)
            if not prop_id or not li_id:
                continue
            session.execute(text("""
                INSERT INTO budgets (tenant_id, property_id, year, month, line_item_id, value)
                VALUES (:tenant_id, :property_id, :year, :month, :line_item_id, :value)
                ON CONFLICT (tenant_id, property_id, year, month, line_item_id)
                DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
            """), {
                "tenant_id": tenant_id,
                "property_id": str(prop_id),
                "year": record.year,
                "month": record.month,
                "line_item_id": str(li_id),
                "value": record.value,
            })
            budget_count += 1

        # Fetch forecasts
        forecast_records = asyncio.get_event_loop().run_until_complete(
            adapter.fetch_forecasts(list(property_map.keys()), today.year)
        )
        forecast_count = 0
        for record in forecast_records:
            prop_id = property_map.get(record.property_code)
            li_id = line_item_map.get(record.account_code)
            if not prop_id or not li_id:
                continue
            session.execute(text("""
                INSERT INTO forecasts (tenant_id, property_id, year, month, line_item_id, value)
                VALUES (:tenant_id, :property_id, :year, :month, :line_item_id, :value)
                ON CONFLICT (tenant_id, property_id, year, month, line_item_id)
                DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
            """), {
                "tenant_id": tenant_id,
                "property_id": str(prop_id),
                "year": record.year,
                "month": record.month,
                "line_item_id": str(li_id),
                "value": record.value,
            })
            forecast_count += 1

        session.commit()

    logger.info(f"Synced {budget_count} budgets, {forecast_count} forecasts for tenant {tenant_id}")
    return {"budgets_synced": budget_count, "forecasts_synced": forecast_count}
