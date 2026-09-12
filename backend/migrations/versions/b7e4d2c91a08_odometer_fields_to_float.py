"""Convert odometer columns from Integer to Float (2dp app rounding).

Revision ID: b7e4d2c91a08
Revises: 2fefc94abc4b
Create Date: 2026-09-11 11:35:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b7e4d2c91a08"
down_revision: Union[str, Sequence[str], None] = "2fefc94abc4b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Allow fractional km readings; app layer rounds to 2 decimals."""
    op.alter_column(
        "vehicles",
        "current_odometer",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=False,
        postgresql_using="current_odometer::double precision",
    )
    op.alter_column(
        "fuel_logs",
        "odometer",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=False,
        postgresql_using="odometer::double precision",
    )
    op.alter_column(
        "service_logs",
        "odometer",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=False,
        postgresql_using="odometer::double precision",
    )
    op.alter_column(
        "service_logs",
        "next_service_odometer",
        existing_type=sa.Integer(),
        type_=sa.Float(),
        existing_nullable=True,
        postgresql_using="next_service_odometer::double precision",
    )


def downgrade() -> None:
    op.alter_column(
        "service_logs",
        "next_service_odometer",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=True,
        postgresql_using="ROUND(next_service_odometer)::integer",
    )
    op.alter_column(
        "service_logs",
        "odometer",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="ROUND(odometer)::integer",
    )
    op.alter_column(
        "fuel_logs",
        "odometer",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="ROUND(odometer)::integer",
    )
    op.alter_column(
        "vehicles",
        "current_odometer",
        existing_type=sa.Float(),
        type_=sa.Integer(),
        existing_nullable=False,
        postgresql_using="ROUND(current_odometer)::integer",
    )
