"""add_execution_jobs_table

Revision ID: 6c7f03514563
Revises: f91ba138bec6
Create Date: 2025-12-08 17:53:04.355353

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6c7f03514563'
down_revision: Union[str, Sequence[str], None] = 'f91ba138bec6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'execution_jobs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('creative_id', sa.Integer(), nullable=True),
        sa.Column('job_type', sa.String(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='QUEUED'),
        sa.Column('retries', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['cam_campaigns.id']),
        sa.ForeignKeyConstraint(['creative_id'], ['creative_assets.id'])
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('execution_jobs')
