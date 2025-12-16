"""add distribution tracking

Revision ID: add_distribution
Revises: add_lead_consent
Create Date: 2025-12-14 17:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_distribution'
down_revision: Union[str, None] = 'add_lead_consent'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create distribution_jobs table
    op.create_table('distribution_jobs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('venture_id', sa.String(), nullable=False),
    sa.Column('campaign_id', sa.Integer(), nullable=False),
    sa.Column('lead_id', sa.Integer(), nullable=False),
    sa.Column('channel', sa.String(), nullable=False),
    sa.Column('message_id', sa.String(), nullable=True),
    sa.Column('status', sa.String(), nullable=False),
    sa.Column('error', sa.Text(), nullable=True),
    sa.Column('executed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['venture_id'], ['ventures.id'], ),
    sa.ForeignKeyConstraint(['campaign_id'], ['cam_campaigns.id'], ),
    sa.ForeignKeyConstraint(['lead_id'], ['cam_leads.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for querying
    op.create_index('idx_distribution_campaign', 'distribution_jobs', ['campaign_id'], unique=False)
    op.create_index('idx_distribution_status', 'distribution_jobs', ['status'], unique=False)
    op.create_index('idx_distribution_lead', 'distribution_jobs', ['lead_id'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_distribution_lead', table_name='distribution_jobs')
    op.drop_index('idx_distribution_status', table_name='distribution_jobs')
    op.drop_index('idx_distribution_campaign', table_name='distribution_jobs')
    op.drop_table('distribution_jobs')
