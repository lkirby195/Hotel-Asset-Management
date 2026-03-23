"""Create forecast_locks table

Revision ID: 005
Revises: 004
Create Date: 2026-03-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "forecast_locks",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("year", sa.SmallInteger, nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False),
        sa.Column("line_item_id", UUID(as_uuid=True), sa.ForeignKey("line_items.id"), nullable=False),
        sa.Column("value", sa.BigInteger, nullable=False, server_default="0"),
        sa.Column("locked_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()")),
        sa.UniqueConstraint(
            "tenant_id", "property_id", "year", "month", "line_item_id",
            name="uq_forecast_locks_key",
        ),
    )
    op.create_index(
        "ix_forecast_locks_prop_year_month",
        "forecast_locks",
        ["property_id", "year", "month"],
    )


def downgrade() -> None:
    op.drop_index("ix_forecast_locks_prop_year_month", table_name="forecast_locks")
    op.drop_table("forecast_locks")
