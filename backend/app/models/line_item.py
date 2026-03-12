import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin


class LineItem(Base, TenantMixin):
    __tablename__ = "line_items"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_line_items_tenant_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("line_items.id"), nullable=True)
    department_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    is_summary: Mapped[bool] = mapped_column(Boolean, server_default="false")
    data_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'revenue' or 'expense'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    parent = relationship("LineItem", remote_side="LineItem.id", back_populates="children")
    children = relationship("LineItem", back_populates="parent", order_by="LineItem.sort_order")
    configs = relationship("LineItemConfig", back_populates="line_item")


class LineItemConfig(Base, TenantMixin):
    __tablename__ = "line_item_config"
    __table_args__ = (
        UniqueConstraint("line_item_id", "report_type", name="uq_line_item_config_item_report"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    line_item_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("line_items.id"), nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    user_role_min: Mapped[str] = mapped_column(String(20), server_default="manager")
    display_format: Mapped[str] = mapped_column(String(20), server_default="currency")

    line_item = relationship("LineItem", back_populates="configs")
