"""add venture and campaign config tables

Revision ID: add_venture_config
Revises: bb0885d50953
Create Date: 2025-12-14 17:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_venture_config'
down_revision: Union[str, None] = 'bb0885d50953'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ventures table
    op.create_table('ventures',
    sa.Column('id', sa.String(), nullable=False),
    sa.Column('venture_name', sa.String(), nullable=False),
    sa.Column('offer_summary', sa.Text(), nullable=False),
    sa.Column('primary_cta', sa.String(), nullable=False),
    sa.Column('default_channels', sa.JSON(), nullable=False),
    sa.Column('timezone', sa.String(), nullable=False),
    sa.Column('owner_contact', sa.String(), nullable=False),
    sa.Column('active', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Create campaign_configs table
    op.create_table('campaign_configs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('campaign_id', sa.Integer(), nullable=False),
    sa.Column('venture_id', sa.String(), nullable=False),
    sa.Column('objective', sa.Text(), nullable=False),
    sa.Column('allowed_channels', sa.JSON(), nullable=False),
    sa.Column('daily_send_limit', sa.Integer(), nullable=False),
    sa.Column('status', sa.Enum('DRAFT', 'RUNNING', 'PAUSED', 'STOPPED', 'COMPLETED', name='campaignstatus'), nullable=False),
    sa.Column('kill_switch', sa.Boolean(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['campaign_id'], ['cam_campaigns.id'], ),
    sa.ForeignKeyConstraint(['venture_id'], ['ventures.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('campaign_id')
    )


def downgrade() -> None:
    op.drop_table('campaign_configs')
    op.drop_table('ventures')
    op.execute('DROP TYPE campaignstatus')
