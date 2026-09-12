"""Add reminders_muted column to vehicles.

Revision ID: c4e8a91b2f70
Revises: b7e4d2c91a08
Create Date: 2026-09-11 09:45:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "c4e8a91b2f70"
down_revision: Union[str, Sequence[str], None] = "b7e4d2c91a08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Existing bikes keep reminders on (false).

    Temporary server_default backfills rows; then drop it so new
    inserts follow the ORM default (also false).
    """
    op.add_column(
        "vehicles",
        sa.Column(
            "reminders_muted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.alter_column("vehicles", "reminders_muted", server_default=None)


def downgrade() -> None:
    op.drop_column("vehicles", "reminders_muted")
