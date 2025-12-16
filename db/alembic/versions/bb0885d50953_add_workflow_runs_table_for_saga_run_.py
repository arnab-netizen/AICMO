"""add workflow_runs table for saga run tracking

Revision ID: bb0885d50953
Revises: 8d6e3cfdc6f9
Create Date: 2025-12-14 15:21:26.794637

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'bb0885d50953'
down_revision: Union[str, Sequence[str], None] = '8d6e3cfdc6f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'workflow_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('brief_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('claimed_by', sa.String(), nullable=True),
        sa.Column('claimed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('lease_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=False, server_default='{}'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_workflow_runs_brief_id', 'workflow_runs', ['brief_id'])
    op.create_index('ix_workflow_runs_status', 'workflow_runs', ['status'])
    op.create_index(
        'ix_workflow_runs_status_claimed_expires',
        'workflow_runs',
        ['status', 'claimed_by', 'lease_expires_at']
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_workflow_runs_status_claimed_expires')
    op.drop_index('ix_workflow_runs_status')
    op.drop_index('ix_workflow_runs_brief_id')
    op.drop_table('workflow_runs')
