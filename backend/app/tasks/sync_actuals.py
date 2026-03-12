import logging
from datetime import date

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session

from app.config import settings
from app.models.line_item import LineItem
from app.models.property import Property
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


def _get_sync_engine():
    """Create a sync SQLAlchemy engine for Celery tasks."""
    return create_engine(settings.database_url_sync)


def _get_adapter():
    """Get the data source adapter (ProfitSword or Mock)."""
    if settings.environment == "development" and not settings.profitsword_username:
        from app.adapters.mock_adapter import MockAdapter
        return MockAdapter()

    from app.adapters.mapping import MappingEngine
    from app.adapters.profitsword import ProfitSwordAdapter
    mapping = MappingEngine.default()
    return ProfitSwordAdapter(
        base_url=settings.profitsword_base_url,
        username=settings.profitsword_username,
        password=settings.profitsword_password,
        mapping=mapping,
        dataset_actuals=settings.profitsword_dataset_actuals,
        dataset_budget=settings.profitsword_dataset_budget,
        dataset_forecast=settings.profitsword_dataset_forecast,
    )


@celery_app.task(bind=True, max_retries=3, name="sync_actuals")
def sync_actuals(self, tenant_id: str):
    """Fetch daily actuals for current + prior month and upsert into DB."""
    import asyncio

    engine = _get_sync_engine()

    with Session(engine) as session:
        # Set RLS context
        session.execute(text(f"SET LOCAL app.current_tenant_id = '{tenant_id}'"))

        # Get all property codes for tenant
        properties = session.execute(
            select(Property.id, Property.code).where(Property.is_active == True)  # noqa: E712
        ).fetchall()
        property_map = {p.code: p.id for p in properties}

        # Build line_item code -> id lookup
        line_items = session.execute(select(LineItem.id, LineItem.code)).fetchall()
        line_item_map = {li.code: li.id for li in line_items}

        # Date range: full current month + full prior month
        today = date.today()
        if today.month == 1:
            prior_start = date(today.year - 1, 12, 1)
        else:
            prior_start = date(today.year, today.month - 1, 1)
        current_end = today

        # Fetch from adapter
        adapter = _get_adapter()
        records = asyncio.get_event_loop().run_until_complete(
            adapter.fetch_daily_actuals(list(property_map.keys()), prior_start, current_end)
        )

        # Batch upsert
        batch = []
        for record in records:
            prop_id = property_map.get(record.property_code)
            li_id = line_item_map.get(record.account_code)
            if not prop_id or not li_id:
                continue

            batch.append({
                "tenant_id": tenant_id,
                "property_id": str(prop_id),
                "date": record.date.isoformat(),
                "line_item_id": str(li_id),
                "value": record.value,
                "per_unit_value": record.per_unit_value,
            })

            if len(batch) >= 500:
                _upsert_batch(session, batch)
                batch = []

        if batch:
            _upsert_batch(session, batch)

        session.commit()

    logger.info(f"Synced {len(records)} actual records for tenant {tenant_id}")
    return {"records_synced": len(records)}


def _upsert_batch(session: Session, batch: list[dict]):
    """Upsert a batch of records into daily_actuals."""
    for row in batch:
        session.execute(text("""
            INSERT INTO daily_actuals (tenant_id, property_id, date, line_item_id, value, per_unit_value)
            VALUES (:tenant_id, :property_id, :date::date, :line_item_id, :value, :per_unit_value)
            ON CONFLICT (tenant_id, property_id, date, line_item_id)
            DO UPDATE SET value = EXCLUDED.value, per_unit_value = EXCLUDED.per_unit_value, updated_at = NOW()
        """), row)
