"""Add available_rooms column to properties

Revision ID: 006
Revises: 005
Create Date: 2026-03-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("properties", sa.Column("available_rooms", sa.Integer, nullable=True))


def downgrade() -> None:
    op.drop_column("properties", "available_rooms")
