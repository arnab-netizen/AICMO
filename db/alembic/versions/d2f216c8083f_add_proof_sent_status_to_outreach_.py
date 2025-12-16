"""add_proof_sent_status_to_outreach_attempts

Revision ID: d2f216c8083f
Revises: a63f66b8f2ec
Create Date: 2025-12-15 05:37:25.107797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd2f216c8083f'
down_revision: Union[str, Sequence[str], None] = 'a63f66b8f2ec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
