"""Create commentary table

Revision ID: 008
Revises: 007
Create Date: 2026-03-25
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "008"
down_revision: Union[str, None] = "007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "commentary",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", UUID(as_uuid=True), sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("property_id", UUID(as_uuid=True), sa.ForeignKey("properties.id"), nullable=False, index=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False, index=True),
        sa.Column("year", sa.Integer, nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False),
        sa.Column("department_tag", sa.String(100), nullable=True),
        sa.Column("category_tag", sa.String(50), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # Index for common query pattern
    op.create_index(
        "ix_commentary_property_year_month",
        "commentary",
        ["property_id", "year", "month"],
    )

    # RLS policy
    op.execute("ALTER TABLE commentary ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY commentary_tenant_isolation ON commentary
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS commentary_tenant_isolation ON commentary")
    op.drop_index("ix_commentary_property_year_month")
    op.drop_table("commentary")
