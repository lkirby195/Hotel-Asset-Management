"""Row-level security policies for multi-tenant isolation

Revision ID: 003
Revises: 002
Create Date: 2026-03-12
"""
from typing import Sequence, Union

from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TENANT_TABLES = [
    "properties",
    "departments",
    "line_items",
    "line_item_config",
    "daily_actuals",
    "monthly_actuals",
    "budgets",
    "forecasts",
    "month_close_status",
    "users",
    "user_properties",
]


def upgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"""
            CREATE POLICY tenant_isolation_{table} ON {table}
            USING (tenant_id = current_setting('app.current_tenant_id', true)::UUID)
        """)
        # Allow the policy to apply to INSERT as well
        op.execute(f"""
            CREATE POLICY tenant_insert_{table} ON {table}
            FOR INSERT
            WITH CHECK (tenant_id = current_setting('app.current_tenant_id', true)::UUID)
        """)


def downgrade() -> None:
    for table in TENANT_TABLES:
        op.execute(f"DROP POLICY IF EXISTS tenant_insert_{table} ON {table}")
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_{table} ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")
