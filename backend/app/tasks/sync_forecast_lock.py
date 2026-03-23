import logging
from datetime import date

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.models.line_item import LineItem
from app.models.property import Property
from app.tasks.celery_app import celery_app
from app.tasks.sync_actuals import _get_adapter, _get_sync_engine

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3, name="lock_monthly_forecast")
def lock_monthly_forecast(self, tenant_id: str, year: int | None = None, month: int | None = None):
    """Snapshot forecast values into forecast_locks for a given month.

    By default locks the prior month (intended to run on day 1).
    Pass explicit year/month to lock a specific period.
    Idempotent: ON CONFLICT UPDATE overwrites existing locks.
    """
    import asyncio

    if (year is None) != (month is None):
        raise ValueError("year and month must both be provided or both be None")

    today = date.today()
    if year is None and month is None:
        # Default: lock previous month
        if today.month == 1:
            year, month = today.year - 1, 12
        else:
            year, month = today.year, today.month - 1

    engine = _get_sync_engine()

    try:
        with Session(engine) as session:
            session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))

            properties = session.execute(
                select(Property.id, Property.code).where(Property.is_active == True)  # noqa: E712
            ).fetchall()
            property_map = {p.code: p.id for p in properties}

            line_items = session.execute(select(LineItem.id, LineItem.code)).fetchall()
            line_item_map = {li.code: li.id for li in line_items}

            adapter = _get_adapter()

            # Fetch forecasts for the target year
            forecast_records = asyncio.run(
                adapter.fetch_forecasts(list(property_map.keys()), year)
            )

            lock_count = 0
            for record in forecast_records:
                if record.month != month:
                    continue

                prop_id = property_map.get(record.property_code)
                li_id = line_item_map.get(record.account_code)
                if not prop_id or not li_id:
                    continue

                session.execute(text("""
                    INSERT INTO forecast_locks (tenant_id, property_id, year, month, line_item_id, value)
                    VALUES (:tenant_id, :property_id, :year, :month, :line_item_id, :value)
                    ON CONFLICT (tenant_id, property_id, year, month, line_item_id)
                    DO UPDATE SET value = EXCLUDED.value, locked_at = NOW()
                """), {
                    "tenant_id": tenant_id,
                    "property_id": str(prop_id),
                    "year": year,
                    "month": month,
                    "line_item_id": str(li_id),
                    "value": record.value,
                })
                lock_count += 1

            session.commit()
    except ValueError:
        raise
    except Exception as exc:
        logger.exception(f"Failed to lock forecasts for {year}-{month}, tenant {tenant_id}")
        raise self.retry(exc=exc)

    logger.info(f"Locked {lock_count} forecast records for {year}-{month:02d}, tenant {tenant_id}")
    return {"forecast_locks": lock_count, "year": year, "month": month}
