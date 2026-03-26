import uuid

from sqlalchemy import BigInteger, ForeignKey, Integer, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TenantMixin, TimestampMixin


class Goal(Base, TenantMixin, TimestampMixin):
    __tablename__ = "goals"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id", "property_id", "user_id", "metric_code", "period_type", "year", "month",
            name="uq_goals_tenant_prop_user_metric_period",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=func.gen_random_uuid(),
    )
    property_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("properties.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    metric_code: Mapped[str] = mapped_column(String(50), nullable=False)
    target_value: Mapped[int] = mapped_column(BigInteger, nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'monthly' or 'annual'
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)  # 0 = annual sentinel

    # Relationships
    property = relationship("Property", lazy="selectin")
    user = relationship("User", lazy="selectin")
