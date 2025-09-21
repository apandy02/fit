"""rename primary to is_primary_tracker

Revision ID: aebc7d8148c6
Revises: a4b1e8c9add9
Create Date: 2025-09-21 18:21:02.615955

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "aebc7d8148c6"
down_revision: Union[str, None] = "a4b1e8c9add9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_tracker_user_primary", table_name="tracker_accounts")
    op.alter_column("tracker_accounts", "primary", new_column_name="is_primary_tracker")
    op.create_index(
        "ix_tracker_user_primary_tracker",
        "tracker_accounts",
        ["user_id", "is_primary_tracker"],
    )


def downgrade() -> None:
    op.drop_index("ix_tracker_user_primary_tracker", table_name="tracker_accounts")
    op.alter_column(
        "tracker_accounts", "is_primary_tracker", new_column_name="primary"
    )  # Recreate the original index
    op.create_index(
        "ix_tracker_user_primary", "tracker_accounts", ["user_id", "primary"]
    )
