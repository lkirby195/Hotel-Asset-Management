"""Materialized views for pre-computed rollups

Revision ID: 002
Revises: 001
Create Date: 2026-03-12
"""
from typing import Sequence, Union

from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- MTD actuals ---
    op.execute("""
        CREATE MATERIALIZED VIEW mv_mtd_actuals AS
        SELECT
            tenant_id,
            property_id,
            line_item_id,
            EXTRACT(YEAR FROM date)::SMALLINT AS year,
            EXTRACT(MONTH FROM date)::SMALLINT AS month,
            SUM(value) AS actual_value
        FROM daily_actuals
        WHERE date >= DATE_TRUNC('month', CURRENT_DATE)
          AND date <= CURRENT_DATE
        GROUP BY tenant_id, property_id, line_item_id,
                 EXTRACT(YEAR FROM date), EXTRACT(MONTH FROM date)
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_mtd
        ON mv_mtd_actuals(tenant_id, property_id, line_item_id, year, month)
    """)

    # --- QTD actuals ---
    op.execute("""
        CREATE MATERIALIZED VIEW mv_qtd_actuals AS
        SELECT
            tenant_id,
            property_id,
            line_item_id,
            EXTRACT(YEAR FROM date)::SMALLINT AS year,
            EXTRACT(QUARTER FROM date)::SMALLINT AS quarter,
            SUM(value) AS actual_value
        FROM daily_actuals
        WHERE date >= DATE_TRUNC('quarter', CURRENT_DATE)
          AND date <= CURRENT_DATE
        GROUP BY tenant_id, property_id, line_item_id,
                 EXTRACT(YEAR FROM date), EXTRACT(QUARTER FROM date)
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_qtd
        ON mv_qtd_actuals(tenant_id, property_id, line_item_id, year, quarter)
    """)

    # --- YTD actuals ---
    op.execute("""
        CREATE MATERIALIZED VIEW mv_ytd_actuals AS
        SELECT
            tenant_id,
            property_id,
            line_item_id,
            EXTRACT(YEAR FROM date)::SMALLINT AS year,
            SUM(value) AS actual_value
        FROM daily_actuals
        WHERE date >= DATE_TRUNC('year', CURRENT_DATE)
          AND date <= CURRENT_DATE
        GROUP BY tenant_id, property_id, line_item_id,
                 EXTRACT(YEAR FROM date)
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_ytd
        ON mv_ytd_actuals(tenant_id, property_id, line_item_id, year)
    """)

    # --- Trailing 28 days ---
    op.execute("""
        CREATE MATERIALIZED VIEW mv_trailing_28 AS
        SELECT
            tenant_id,
            property_id,
            line_item_id,
            SUM(value) AS actual_value
        FROM daily_actuals
        WHERE date >= CURRENT_DATE - INTERVAL '28 days'
          AND date <= CURRENT_DATE
        GROUP BY tenant_id, property_id, line_item_id
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_t28
        ON mv_trailing_28(tenant_id, property_id, line_item_id)
    """)

    # --- Weekly actuals (ISO week) ---
    op.execute("""
        CREATE MATERIALIZED VIEW mv_weekly_actuals AS
        SELECT
            tenant_id,
            property_id,
            line_item_id,
            EXTRACT(ISOYEAR FROM date)::SMALLINT AS iso_year,
            EXTRACT(WEEK FROM date)::SMALLINT AS iso_week,
            SUM(value) AS actual_value
        FROM daily_actuals
        WHERE date >= CURRENT_DATE - INTERVAL '8 weeks'
          AND date <= CURRENT_DATE
        GROUP BY tenant_id, property_id, line_item_id,
                 EXTRACT(ISOYEAR FROM date), EXTRACT(WEEK FROM date)
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_weekly
        ON mv_weekly_actuals(tenant_id, property_id, line_item_id, iso_year, iso_week)
    """)

    # --- Variance: Actual vs Budget (MTD) ---
    op.execute("""
        CREATE MATERIALIZED VIEW mv_variance_budget AS
        SELECT
            m.tenant_id,
            m.property_id,
            m.line_item_id,
            m.year,
            m.month,
            m.actual_value,
            b.value AS budget_value,
            (m.actual_value - b.value) AS variance_dollars,
            CASE WHEN b.value != 0
                 THEN ROUND(((m.actual_value - b.value)::NUMERIC / b.value) * 100, 2)
                 ELSE NULL
            END AS variance_pct
        FROM mv_mtd_actuals m
        LEFT JOIN budgets b
            ON m.tenant_id = b.tenant_id
           AND m.property_id = b.property_id
           AND m.line_item_id = b.line_item_id
           AND m.year = b.year
           AND m.month = b.month
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_var_budget
        ON mv_variance_budget(tenant_id, property_id, line_item_id, year, month)
    """)

    # --- Variance: Actual vs Forecast (MTD) ---
    op.execute("""
        CREATE MATERIALIZED VIEW mv_variance_forecast AS
        SELECT
            m.tenant_id,
            m.property_id,
            m.line_item_id,
            m.year,
            m.month,
            m.actual_value,
            f.value AS forecast_value,
            (m.actual_value - f.value) AS variance_dollars,
            CASE WHEN f.value != 0
                 THEN ROUND(((m.actual_value - f.value)::NUMERIC / f.value) * 100, 2)
                 ELSE NULL
            END AS variance_pct
        FROM mv_mtd_actuals m
        LEFT JOIN forecasts f
            ON m.tenant_id = f.tenant_id
           AND m.property_id = f.property_id
           AND m.line_item_id = f.line_item_id
           AND m.year = f.year
           AND m.month = f.month
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_var_forecast
        ON mv_variance_forecast(tenant_id, property_id, line_item_id, year, month)
    """)

    # --- Variance: Actual vs Prior Year (MTD) ---
    op.execute("""
        CREATE MATERIALIZED VIEW mv_variance_py AS
        SELECT
            curr.tenant_id,
            curr.property_id,
            curr.line_item_id,
            curr.year,
            curr.month,
            curr.actual_value AS current_value,
            py.actual_value AS py_value,
            (curr.actual_value - COALESCE(py.actual_value, 0)) AS variance_dollars,
            CASE WHEN COALESCE(py.actual_value, 0) != 0
                 THEN ROUND(((curr.actual_value - py.actual_value)::NUMERIC / py.actual_value) * 100, 2)
                 ELSE NULL
            END AS variance_pct
        FROM mv_mtd_actuals curr
        LEFT JOIN mv_mtd_actuals py
            ON curr.tenant_id = py.tenant_id
           AND curr.property_id = py.property_id
           AND curr.line_item_id = py.line_item_id
           AND curr.year = py.year + 1
           AND curr.month = py.month
    """)
    op.execute("""
        CREATE UNIQUE INDEX idx_mv_var_py
        ON mv_variance_py(tenant_id, property_id, line_item_id, year, month)
    """)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_variance_py CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_variance_forecast CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_variance_budget CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_weekly_actuals CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_trailing_28 CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_ytd_actuals CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_qtd_actuals CASCADE")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS mv_mtd_actuals CASCADE")
