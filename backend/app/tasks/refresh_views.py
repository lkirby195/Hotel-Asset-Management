import logging

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.tasks.celery_app import celery_app
from app.tasks.sync_actuals import _get_sync_engine

logger = logging.getLogger(__name__)

# Order matters: base views first, then variance views that depend on them
MATERIALIZED_VIEWS = [
    "mv_mtd_actuals",
    "mv_qtd_actuals",
    "mv_ytd_actuals",
    "mv_trailing_28",
    "mv_weekly_actuals",
    "mv_variance_budget",
    "mv_variance_forecast",
    "mv_variance_py",
]


@celery_app.task(name="refresh_views")
def refresh_materialized_views(tenant_id: str):
    """Refresh all materialized views in dependency order.

    Uses CONCURRENTLY to allow reads during refresh.
    """
    engine = _get_sync_engine()

    with Session(engine) as session:
        for view in MATERIALIZED_VIEWS:
            try:
                session.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view}"))
                session.commit()
                logger.info(f"Refreshed {view}")
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to refresh {view}: {e}")
                # Try non-concurrent refresh as fallback (first refresh after creation)
                try:
                    session.execute(text(f"REFRESH MATERIALIZED VIEW {view}"))
                    session.commit()
                    logger.info(f"Refreshed {view} (non-concurrent fallback)")
                except Exception as e2:
                    session.rollback()
                    logger.error(f"Non-concurrent refresh also failed for {view}: {e2}")

    return {"views_refreshed": len(MATERIALIZED_VIEWS)}
