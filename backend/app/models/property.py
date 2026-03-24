import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin


class Property(Base, TenantMixin, TimestampMixin):
    __tablename__ = "properties"
    __table_args__ = (
        UniqueConstraint("tenant_id", "code", name="uq_properties_tenant_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=func.gen_random_uuid())
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    timezone: Mapped[str] = mapped_column(String(50), server_default="America/New_York")
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true")
    available_rooms: Mapped[int | None] = mapped_column(Integer, nullable=True)

    tenant = relationship("Tenant", back_populates="properties")
    departments = relationship("Department", back_populates="property")
    users = relationship("User", secondary="user_properties", back_populates="properties")
