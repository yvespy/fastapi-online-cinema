"""seed user groups

Revision ID: 32ce4995e9d5
Revises: df0bdc3367a2
Create Date: 2025-12-17 18:03:21.712129

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '32ce4995e9d5'
down_revision: Union[str, Sequence[str], None] = 'df0bdc3367a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_groups = sa.table(
        "user_groups",
        sa.column("id", sa.Integer),
        sa.column("name", sa.Enum("USER", "MODERATOR", "ADMIN", name="usergroupenum")),
    )

    op.bulk_insert(
        user_groups,
        [
            {"id": 1, "name": "USER"},
            {"id": 2, "name": "MODERATOR"},
            {"id": 3, "name": "ADMIN"},
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM user_groups")
