"""add_campaign_strategy_fields

Revision ID: a812cd322779
Revises: 5e3a9d7f2b4c
Create Date: 2025-12-08 13:38:01.659176

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a812cd322779'
down_revision: Union[str, Sequence[str], None] = '5e3a9d7f2b4c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Add strategy document storage fields
    op.add_column('cam_campaigns', sa.Column('strategy_text', sa.Text(), nullable=True))
    op.add_column('cam_campaigns', sa.Column('strategy_status', sa.String(), nullable=True, server_default='DRAFT'))
    op.add_column('cam_campaigns', sa.Column('strategy_rejection_reason', sa.Text(), nullable=True))
    
    # Add intake context fields
    op.add_column('cam_campaigns', sa.Column('intake_goal', sa.Text(), nullable=True))
    op.add_column('cam_campaigns', sa.Column('intake_constraints', sa.Text(), nullable=True))
    op.add_column('cam_campaigns', sa.Column('intake_audience', sa.Text(), nullable=True))
    op.add_column('cam_campaigns', sa.Column('intake_budget', sa.String(), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    # Remove all added columns
    op.drop_column('cam_campaigns', 'intake_budget')
    op.drop_column('cam_campaigns', 'intake_audience')
    op.drop_column('cam_campaigns', 'intake_constraints')
    op.drop_column('cam_campaigns', 'intake_goal')
    op.drop_column('cam_campaigns', 'strategy_rejection_reason')
    op.drop_column('cam_campaigns', 'strategy_status')
    op.drop_column('cam_campaigns', 'strategy_text')

