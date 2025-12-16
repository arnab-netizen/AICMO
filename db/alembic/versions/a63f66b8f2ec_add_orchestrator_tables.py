"""add_orchestrator_tables

Adds tables for Campaign Orchestrator (Phase 2 Fast Revenue Engine):
- cam_orchestrator_runs: Single-writer lease + run state
- cam_unsubscribes: Unsubscribe list
- cam_suppressions: Suppression list (email/domain/identity_hash)
- Idempotency constraint on distribution_jobs

Revision ID: a63f66b8f2ec
Revises: 71751d732ad2
Create Date: 2025-12-14 19:28:32.073340

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a63f66b8f2ec'
down_revision: Union[str, Sequence[str], None] = '71751d732ad2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add orchestrator tables and idempotency constraints."""
    
    # Orchestrator run state with lease
    op.create_table(
        'cam_orchestrator_runs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('claimed_by', sa.String(), nullable=False),
        sa.Column('lease_expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('heartbeat_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('leads_processed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('jobs_created', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('attempts_succeeded', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('attempts_failed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_orchestrator_campaign_status', 'cam_orchestrator_runs', ['campaign_id', 'status'])
    op.create_index('idx_orchestrator_lease', 'cam_orchestrator_runs', ['campaign_id', 'lease_expires_at'])
    op.create_index('idx_orchestrator_campaign', 'cam_orchestrator_runs', ['campaign_id'])
    
    # Unsubscribe list
    op.create_table(
        'cam_unsubscribes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('reason', sa.String(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('unsubscribed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_unsubscribe_email')
    )
    op.create_index('idx_unsubscribe_email', 'cam_unsubscribes', ['email'])
    
    # Suppression list
    op.create_table(
        'cam_suppressions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('identity_hash', sa.String(), nullable=True),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_suppression_email', 'cam_suppressions', ['email', 'active'])
    op.create_index('idx_suppression_domain', 'cam_suppressions', ['domain', 'active'])
    op.create_index('idx_suppression_hash', 'cam_suppressions', ['identity_hash', 'active'])
    
    # Add idempotency constraint to distribution_jobs
    # Format: campaign_id + lead_id + message_id = unique per dispatch
    op.add_column('distribution_jobs', sa.Column('idempotency_key', sa.String(), nullable=True))
    op.create_index('idx_distribution_idempotency', 'distribution_jobs', ['idempotency_key'], unique=True)
    
    # Add retry tracking to distribution_jobs
    op.add_column('distribution_jobs', sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('distribution_jobs', sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'))
    op.add_column('distribution_jobs', sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('distribution_jobs', sa.Column('step_index', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove orchestrator tables and constraints."""
    
    # Remove distribution_jobs additions
    op.drop_index('idx_distribution_idempotency', 'distribution_jobs')
    op.drop_column('distribution_jobs', 'step_index')
    op.drop_column('distribution_jobs', 'next_retry_at')
    op.drop_column('distribution_jobs', 'max_retries')
    op.drop_column('distribution_jobs', 'retry_count')
    op.drop_column('distribution_jobs', 'idempotency_key')
    
    # Drop suppression table
    op.drop_index('idx_suppression_hash', 'cam_suppressions')
    op.drop_index('idx_suppression_domain', 'cam_suppressions')
    op.drop_index('idx_suppression_email', 'cam_suppressions')
    op.drop_table('cam_suppressions')
    
    # Drop unsubscribe table
    op.drop_index('idx_unsubscribe_email', 'cam_unsubscribes')
    op.drop_table('cam_unsubscribes')
    
    # Drop orchestrator runs table
    op.drop_index('idx_orchestrator_campaign', 'cam_orchestrator_runs')
    op.drop_index('idx_orchestrator_lease', 'cam_orchestrator_runs')
    op.drop_index('idx_orchestrator_campaign_status', 'cam_orchestrator_runs')
    op.drop_table('cam_orchestrator_runs')

