"""add_safety_settings_system_paused

Revision ID: 308887b163f4
Revises: a812cd322779
Create Date: 2025-12-08 13:42:53.867806

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '308887b163f4'
down_revision: Union[str, Sequence[str], None] = 'a812cd322779'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add system pause flag to safety settings
    op.add_column('cam_safety_settings', sa.Column('system_paused', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('cam_safety_settings', 'system_paused')

