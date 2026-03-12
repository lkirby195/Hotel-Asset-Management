from celery import chain

from app.tasks.celery_app import celery_app
from app.tasks.invalidate_cache import invalidate_cache_after_sync
from app.tasks.refresh_views import refresh_materialized_views
from app.tasks.sync_actuals import sync_actuals
from app.tasks.sync_budgets import sync_budgets


@celery_app.task(name="run_sync_pipeline")
def run_sync_pipeline(tenant_id: str):
    """Execute the full sync pipeline as a Celery chain.

    Order: sync_actuals → sync_budgets → refresh_views → invalidate_cache
    """
    pipeline = chain(
        sync_actuals.s(tenant_id),
        sync_budgets.si(tenant_id),
        refresh_materialized_views.si(tenant_id),
        invalidate_cache_after_sync.si(tenant_id),
    )
    return pipeline.apply_async()
