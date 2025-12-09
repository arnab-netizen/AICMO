"""add_campaign_project_state

Revision ID: fa9783d90970
Revises: 308887b163f4
Create Date: 2025-12-08 17:15:41.073531

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'fa9783d90970'
down_revision: Union[str, Sequence[str], None] = '308887b163f4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add project_state column to cam_campaigns."""
    op.add_column('cam_campaigns', sa.Column('project_state', sa.String(), nullable=True, server_default='STRATEGY_DRAFT'))


def downgrade() -> None:
    """Downgrade schema - remove project_state column."""
    op.drop_column('cam_campaigns', 'project_state')
