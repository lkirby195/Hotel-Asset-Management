import logging

from app.tasks.celery_app import celery_app
from app.tasks.invalidate_cache import invalidate_cache_after_sync
from app.tasks.refresh_views import refresh_materialized_views
from app.tasks.sync_actuals import sync_actuals
from app.tasks.sync_budgets import sync_budgets

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="run_sync_pipeline")
def run_sync_pipeline(self, tenant_id: str):
    """Execute the full sync pipeline sequentially.

    Order: sync_actuals → sync_budgets → refresh_views → invalidate_cache

    Runs steps directly (not as a chain) so the single task_id
    can be polled for overall status from the admin endpoint.
    """
    logger.info(f"Starting sync pipeline for tenant {tenant_id}")

    self.update_state(state="PROGRESS", meta={"step": "sync_actuals"})
    actuals_result = sync_actuals(tenant_id)

    self.update_state(state="PROGRESS", meta={"step": "sync_budgets"})
    budgets_result = sync_budgets(tenant_id)

    self.update_state(state="PROGRESS", meta={"step": "refresh_views"})
    views_result = refresh_materialized_views(tenant_id)

    self.update_state(state="PROGRESS", meta={"step": "invalidate_cache"})
    cache_result = invalidate_cache_after_sync(tenant_id)

    logger.info(f"Sync pipeline complete for tenant {tenant_id}")
    return {
        "actuals": actuals_result,
        "budgets": budgets_result,
        "views": views_result,
        "cache": cache_result,
    }
