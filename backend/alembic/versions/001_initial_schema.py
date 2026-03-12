"""Initial schema - all Phase 1 tables

Revision ID: 001
Revises: None
Create Date: 2026-03-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable uuid extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # --- tenants ---
    op.create_table(
        "tenants",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), unique=True, nullable=False),
        sa.Column("branding_config", JSONB, server_default=sa.text("'{}'::jsonb")),
        sa.Column("domain", sa.String(255)),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
    )

    # --- users (created before properties so month_close_status can reference it) ---
    op.create_table(
        "users",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("clerk_id", sa.String(255), unique=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(20), nullable=False, server_default=sa.text("'manager'")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
    )

    # --- properties ---
    op.create_table(
        "properties",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("code", sa.String(50), nullable=False),
        sa.Column("timezone", sa.String(50), server_default=sa.text("'America/New_York'")),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "code", name="uq_properties_tenant_code"),
    )

    # --- departments ---
    op.create_table(
        "departments",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("property_id", UUID, sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean, server_default=sa.text("true")),
        sa.UniqueConstraint("property_id", "type", name="uq_departments_property_type"),
    )

    # --- line_items (hierarchical COA) ---
    op.create_table(
        "line_items",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("code", sa.String(100), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("parent_id", UUID, sa.ForeignKey("line_items.id"), nullable=True),
        sa.Column("department_type", sa.String(50), nullable=True),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default=sa.text("0")),
        sa.Column("is_summary", sa.Boolean, server_default=sa.text("false")),
        sa.Column("data_type", sa.String(20), nullable=False),  # 'revenue' or 'expense'
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint("tenant_id", "code", name="uq_line_items_tenant_code"),
    )
    op.create_index("idx_line_items_parent", "line_items", ["parent_id"])
    op.create_index("idx_line_items_dept", "line_items", ["tenant_id", "department_type"])

    # --- line_item_config ---
    op.create_table(
        "line_item_config",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("line_item_id", UUID, sa.ForeignKey("line_items.id"), nullable=False),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False, index=True),
        sa.Column("report_type", sa.String(50), nullable=False),
        sa.Column("user_role_min", sa.String(20), server_default=sa.text("'manager'")),
        sa.Column("display_format", sa.String(20), server_default=sa.text("'currency'")),
        sa.UniqueConstraint("line_item_id", "report_type", name="uq_line_item_config_item_report"),
    )

    # --- daily_actuals ---
    op.create_table(
        "daily_actuals",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("property_id", UUID, sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("date", sa.Date, nullable=False),
        sa.Column("line_item_id", UUID, sa.ForeignKey("line_items.id"), nullable=False),
        sa.Column("value", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("per_unit_value", sa.BigInteger, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "tenant_id", "property_id", "date", "line_item_id",
            name="uq_daily_actuals_key",
        ),
    )
    op.create_index("idx_daily_actuals_lookup", "daily_actuals", ["tenant_id", "property_id", "date"])
    op.create_index(
        "idx_daily_actuals_range", "daily_actuals",
        ["tenant_id", "property_id", "line_item_id", "date"],
    )

    # --- monthly_actuals ---
    op.create_table(
        "monthly_actuals",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("property_id", UUID, sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("year", sa.SmallInteger, nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False),
        sa.Column("line_item_id", UUID, sa.ForeignKey("line_items.id"), nullable=False),
        sa.Column("value", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "tenant_id", "property_id", "year", "month", "line_item_id",
            name="uq_monthly_actuals_key",
        ),
    )

    # --- budgets ---
    op.create_table(
        "budgets",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("property_id", UUID, sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("year", sa.SmallInteger, nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False),
        sa.Column("line_item_id", UUID, sa.ForeignKey("line_items.id"), nullable=False),
        sa.Column("value", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "tenant_id", "property_id", "year", "month", "line_item_id",
            name="uq_budgets_key",
        ),
    )

    # --- forecasts ---
    op.create_table(
        "forecasts",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("property_id", UUID, sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("year", sa.SmallInteger, nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False),
        sa.Column("line_item_id", UUID, sa.ForeignKey("line_items.id"), nullable=False),
        sa.Column("value", sa.BigInteger, nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.UniqueConstraint(
            "tenant_id", "property_id", "year", "month", "line_item_id",
            name="uq_forecasts_key",
        ),
    )

    # --- month_close_status ---
    op.create_table(
        "month_close_status",
        sa.Column("id", UUID, server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("property_id", UUID, sa.ForeignKey("properties.id"), nullable=False),
        sa.Column("year", sa.SmallInteger, nullable=False),
        sa.Column("month", sa.SmallInteger, nullable=False),
        sa.Column("is_closed", sa.Boolean, server_default=sa.text("false")),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_by", UUID, sa.ForeignKey("users.id"), nullable=True),
        sa.UniqueConstraint(
            "tenant_id", "property_id", "year", "month",
            name="uq_month_close_status_key",
        ),
    )

    # --- user_properties ---
    op.create_table(
        "user_properties",
        sa.Column("user_id", UUID, sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("property_id", UUID, sa.ForeignKey("properties.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("tenant_id", UUID, sa.ForeignKey("tenants.id"), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("user_properties")
    op.drop_table("month_close_status")
    op.drop_table("forecasts")
    op.drop_table("budgets")
    op.drop_table("monthly_actuals")
    op.drop_table("daily_actuals")
    op.drop_table("line_item_config")
    op.drop_table("line_items")
    op.drop_table("departments")
    op.drop_table("properties")
    op.drop_table("users")
    op.drop_table("tenants")
