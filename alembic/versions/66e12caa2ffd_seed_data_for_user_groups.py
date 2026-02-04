"""seed data for user groups

Revision ID: 66e12caa2ffd
Revises: 4e9bbca0d153
Create Date: 2025-12-18 02:37:21.655211

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '66e12caa2ffd'
down_revision: Union[str, Sequence[str], None] = '7516fb0e9ef7'
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
    """Downgrade schema."""
    op.execute("DELETE FROM user_groups")
