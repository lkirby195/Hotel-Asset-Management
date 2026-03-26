"""Create goals table

Revision ID: 007
Revises: 006
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "007"
down_revision: Union[str, None] = "006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "goals",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("metric_code", sa.String(50), nullable=False),
        sa.Column("target_value", sa.BigInteger, nullable=False),
        sa.Column("period_type", sa.String(20), nullable=False),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "tenant_id", "property_id", "user_id", "metric_code", "period_type", "year", "month",
            name="uq_goals_tenant_prop_user_metric_period",
        ),
    )

    # RLS policy
    op.execute("ALTER TABLE goals ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY goals_tenant_isolation ON goals
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS goals_tenant_isolation ON goals")
    op.drop_table("goals")
