"""add_cam_tables

Revision ID: 3b1561457c07
Revises: 8f6f0504e89a
Create Date: 2025-12-08 09:49:34.422705

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3b1561457c07'
down_revision: Union[str, Sequence[str], None] = '8f6f0504e89a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add CAM tables."""
    # Create cam_campaigns table
    op.create_table(
        'cam_campaigns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('target_niche', sa.String(), nullable=True),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    
    # Create cam_leads table
    op.create_table(
        'cam_leads',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('company', sa.String(), nullable=True),
        sa.Column('role', sa.String(), nullable=True),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('linkedin_url', sa.String(), nullable=True),
        sa.Column('source', sa.Enum('csv', 'apollo', 'manual', 'other', name='leadsource'), nullable=False, server_default='other'),
        sa.Column('status', sa.Enum('NEW', 'ENRICHED', 'CONTACTED', 'REPLIED', 'QUALIFIED', 'LOST', name='leadstatus'), nullable=False, server_default='NEW'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['campaign_id'], ['cam_campaigns.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create cam_outreach_attempts table
    op.create_table(
        'cam_outreach_attempts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.Enum('linkedin', 'email', 'other', name='channel'), nullable=False),
        sa.Column('step_number', sa.Integer(), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'SENT', 'FAILED', 'SKIPPED', name='attemptstatus'), nullable=False, server_default='PENDING'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['campaign_id'], ['cam_campaigns.id']),
        sa.ForeignKeyConstraint(['lead_id'], ['cam_leads.id']),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema - remove CAM tables."""
    op.drop_table('cam_outreach_attempts')
    op.drop_table('cam_leads')
    op.drop_table('cam_campaigns')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS attemptstatus')
    op.execute('DROP TYPE IF EXISTS channel')
    op.execute('DROP TYPE IF EXISTS leadstatus')
    op.execute('DROP TYPE IF EXISTS leadsource')
