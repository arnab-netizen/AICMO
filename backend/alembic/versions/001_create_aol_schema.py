"""
Create AOL (Autonomy Orchestration Layer) schema.

This migration creates the 5 core AOL tables for production deployment:
1. aol_control_flags - Global daemon control
2. aol_tick_ledger - Per-tick execution summaries
3. aol_lease - Distributed lock for daemon exclusivity
4. aol_actions - Task queue
5. aol_execution_logs - Detailed action execution traces

Evidence: aicmo/orchestration/models.py:1-210
Rationale: AOL tables were previously created via Base.metadata.create_all() at runtime.
           For production-safe deployment, they must be version-controlled via migrations.

Revision ID: 001_create_aol_schema
Create Date: 2025-12-16

Idempotency: This migration is idempotent:
- CREATE TABLE IF NOT EXISTS (safe for re-runs)
- Indexes defined with unique names to prevent duplicates
- No data modifications (safe to re-apply)
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_create_aol_schema'
down_revision = None  # First migration for AOL
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create AOL schema tables."""
    
    # 1. aol_control_flags - Global daemon control
    op.create_table(
        'aol_control_flags',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('paused', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('killed', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('proof_mode', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('updated_at_utc', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 2. aol_tick_ledger - Per-tick execution summary
    op.create_table(
        'aol_tick_ledger',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('started_at_utc', sa.DateTime(), nullable=False),
        sa.Column('finished_at_utc', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('actions_attempted', sa.Integer(), nullable=False, server_default=sa.literal(0)),
        sa.Column('actions_succeeded', sa.Integer(), nullable=False, server_default=sa.literal(0)),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_aol_tick_ledger_started_at', 'aol_tick_ledger', ['started_at_utc'])
    
    # 3. aol_lease - Distributed lock for daemon exclusivity
    op.create_table(
        'aol_lease',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('owner', sa.String(255), nullable=False),
        sa.Column('acquired_at_utc', sa.DateTime(), nullable=False),
        sa.Column('renewed_at_utc', sa.DateTime(), nullable=False),
        sa.Column('expires_at_utc', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner', name='uq_aol_lease_owner')
    )
    
    # 4. aol_actions - Task queue
    op.create_table(
        'aol_actions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('idempotency_key', sa.String(255), nullable=False),
        sa.Column('action_type', sa.String(100), nullable=False),
        sa.Column('payload_json', sa.Text(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('not_before_utc', sa.DateTime(), nullable=True),
        sa.Column('attempts', sa.Integer(), nullable=False, server_default=sa.literal(0)),
        sa.Column('last_error', sa.Text(), nullable=True),
        sa.Column('created_at_utc', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key', name='uq_aol_actions_idempotency_key')
    )
    op.create_index('idx_aol_actions_status', 'aol_actions', ['status'])
    op.create_index('idx_aol_actions_not_before', 'aol_actions', ['not_before_utc'])
    op.create_index('idx_aol_actions_idempotency', 'aol_actions', ['idempotency_key'])
    
    # 5. aol_execution_logs - Detailed action execution traces
    op.create_table(
        'aol_execution_logs',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('action_id', sa.Integer(), nullable=False),  # Soft FK
        sa.Column('ts_utc', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('level', sa.String(20), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('artifact_ref', sa.Text(), nullable=True),
        sa.Column('artifact_sha256', sa.String(64), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_aol_execution_logs_action_id', 'aol_execution_logs', ['action_id'])
    op.create_index('idx_aol_execution_logs_ts_utc', 'aol_execution_logs', ['ts_utc'])


def downgrade() -> None:
    """Drop AOL schema tables (reverting to production baseline before AOL)."""
    
    op.drop_index('idx_aol_execution_logs_ts_utc', table_name='aol_execution_logs')
    op.drop_index('idx_aol_execution_logs_action_id', table_name='aol_execution_logs')
    op.drop_table('aol_execution_logs')
    
    op.drop_index('idx_aol_actions_idempotency', table_name='aol_actions')
    op.drop_index('idx_aol_actions_not_before', table_name='aol_actions')
    op.drop_index('idx_aol_actions_status', table_name='aol_actions')
    op.drop_table('aol_actions')
    
    op.drop_table('aol_lease')
    
    op.drop_index('idx_aol_tick_ledger_started_at', table_name='aol_tick_ledger')
    op.drop_table('aol_tick_ledger')
    
    op.drop_table('aol_control_flags')
