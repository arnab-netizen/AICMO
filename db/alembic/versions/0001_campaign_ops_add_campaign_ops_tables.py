"""add_campaign_ops_tables

Revision ID: 0001_campaign_ops
Revises: d2f216c8083f
Create Date: 2025-12-16 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_campaign_ops'
down_revision: Union[str, Sequence[str], None] = 'd2f216c8083f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create campaign_ops tables."""
    
    # campaign_ops_campaigns
    op.create_table(
        'campaign_ops_campaigns',
        sa.Column('id', sa.Integer, nullable=False, primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('client_name', sa.String(255), nullable=False),
        sa.Column('venture_name', sa.String(255), nullable=True),
        sa.Column('objective', sa.Text, nullable=False),
        sa.Column('platforms', sa.JSON, nullable=False),
        sa.Column('start_date', sa.DateTime, nullable=False),
        sa.Column('end_date', sa.DateTime, nullable=False),
        sa.Column('cadence', sa.JSON, nullable=False),
        sa.Column('primary_cta', sa.String(255), nullable=False),
        sa.Column('lead_capture_method', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='PLANNED'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_campaign_ops_campaigns_name', 'campaign_ops_campaigns', ['name'], unique=True)
    op.create_index('ix_campaign_ops_campaigns_status', 'campaign_ops_campaigns', ['status'])
    op.create_index('ix_campaign_ops_campaigns_created_at', 'campaign_ops_campaigns', ['created_at'])
    op.create_index('ix_campaign_ops_campaigns_status_created', 'campaign_ops_campaigns', ['status', 'created_at'])

    # campaign_ops_plans
    op.create_table(
        'campaign_ops_plans',
        sa.Column('id', sa.Integer, nullable=False, primary_key=True),
        sa.Column('campaign_id', sa.Integer, nullable=False),
        sa.Column('angles_json', sa.JSON, nullable=True),
        sa.Column('positioning_json', sa.JSON, nullable=True),
        sa.Column('messaging_json', sa.JSON, nullable=True),
        sa.Column('weekly_themes_json', sa.JSON, nullable=True),
        sa.Column('generated_by', sa.String(50), nullable=False, server_default='manual'),
        sa.Column('version', sa.Integer, nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign_ops_campaigns.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_campaign_ops_plans_campaign_id', 'campaign_ops_plans', ['campaign_id'])
    op.create_index('ix_campaign_ops_plans_campaign_version', 'campaign_ops_plans', ['campaign_id', 'version'])

    # campaign_ops_calendar_items
    op.create_table(
        'campaign_ops_calendar_items',
        sa.Column('id', sa.Integer, nullable=False, primary_key=True),
        sa.Column('campaign_id', sa.Integer, nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('content_type', sa.String(50), nullable=False, server_default='post'),
        sa.Column('scheduled_at', sa.DateTime, nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('copy_text', sa.Text, nullable=True),
        sa.Column('asset_ref', sa.String(512), nullable=True),
        sa.Column('cta_text', sa.String(255), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign_ops_campaigns.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_campaign_ops_calendar_items_campaign_id', 'campaign_ops_calendar_items', ['campaign_id'])
    op.create_index('ix_campaign_ops_calendar_items_scheduled_at', 'campaign_ops_calendar_items', ['scheduled_at'])
    op.create_index('ix_campaign_ops_calendar_items_status', 'campaign_ops_calendar_items', ['status'])
    op.create_index('ix_campaign_ops_calendar_items_campaign_scheduled', 'campaign_ops_calendar_items', ['campaign_id', 'scheduled_at'])
    op.create_index('ix_campaign_ops_calendar_items_platform_status', 'campaign_ops_calendar_items', ['platform', 'status'])

    # campaign_ops_operator_tasks
    op.create_table(
        'campaign_ops_operator_tasks',
        sa.Column('id', sa.Integer, nullable=False, primary_key=True),
        sa.Column('campaign_id', sa.Integer, nullable=False),
        sa.Column('calendar_item_id', sa.Integer, nullable=True),
        sa.Column('task_type', sa.String(50), nullable=False, server_default='POST'),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('due_at', sa.DateTime, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('instructions_text', sa.Text, nullable=False),
        sa.Column('copy_text', sa.Text, nullable=True),
        sa.Column('asset_ref', sa.String(512), nullable=True),
        sa.Column('status', sa.String(20), nullable=False, server_default='PENDING'),
        sa.Column('completion_proof_type', sa.String(50), nullable=True),
        sa.Column('completion_proof_value', sa.Text, nullable=True),
        sa.Column('completed_at', sa.DateTime, nullable=True),
        sa.Column('blocked_reason', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign_ops_campaigns.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['calendar_item_id'], ['campaign_ops_calendar_items.id'], ondelete='SET NULL'),
    )
    op.create_index('ix_campaign_ops_operator_tasks_campaign_id', 'campaign_ops_operator_tasks', ['campaign_id'])
    op.create_index('ix_campaign_ops_operator_tasks_calendar_item_id', 'campaign_ops_operator_tasks', ['calendar_item_id'])
    op.create_index('ix_campaign_ops_operator_tasks_due_at', 'campaign_ops_operator_tasks', ['due_at'])
    op.create_index('ix_campaign_ops_operator_tasks_status', 'campaign_ops_operator_tasks', ['status'])
    op.create_index('ix_campaign_ops_operator_tasks_campaign_due', 'campaign_ops_operator_tasks', ['campaign_id', 'due_at'])
    op.create_index('ix_campaign_ops_operator_tasks_platform_status', 'campaign_ops_operator_tasks', ['platform', 'status'])
    op.create_index('ix_campaign_ops_operator_tasks_status_due', 'campaign_ops_operator_tasks', ['status', 'due_at'])

    # campaign_ops_metric_entries
    op.create_table(
        'campaign_ops_metric_entries',
        sa.Column('id', sa.Integer, nullable=False, primary_key=True),
        sa.Column('campaign_id', sa.Integer, nullable=False),
        sa.Column('platform', sa.String(50), nullable=False),
        sa.Column('date', sa.DateTime, nullable=False),
        sa.Column('metric_name', sa.String(100), nullable=False),
        sa.Column('metric_value', sa.Float, nullable=False),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['campaign_ops_campaigns.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_campaign_ops_metric_entries_campaign_id', 'campaign_ops_metric_entries', ['campaign_id'])
    op.create_index('ix_campaign_ops_metric_entries_platform', 'campaign_ops_metric_entries', ['platform'])
    op.create_index('ix_campaign_ops_metric_entries_date', 'campaign_ops_metric_entries', ['date'])
    op.create_index('ix_campaign_ops_metric_entries_campaign_date', 'campaign_ops_metric_entries', ['campaign_id', 'date'])
    op.create_index('ix_campaign_ops_metric_entries_platform_metric', 'campaign_ops_metric_entries', ['platform', 'metric_name'])

    # campaign_ops_audit_log
    op.create_table(
        'campaign_ops_audit_log',
        sa.Column('id', sa.Integer, nullable=False, primary_key=True),
        sa.Column('actor', sa.String(100), nullable=False),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', sa.Integer, nullable=True),
        sa.Column('before_json', sa.JSON, nullable=True),
        sa.Column('after_json', sa.JSON, nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_campaign_ops_audit_log_actor', 'campaign_ops_audit_log', ['actor'])
    op.create_index('ix_campaign_ops_audit_log_created_at', 'campaign_ops_audit_log', ['created_at'])
    op.create_index('ix_campaign_ops_audit_log_actor_created', 'campaign_ops_audit_log', ['actor', 'created_at'])
    op.create_index('ix_campaign_ops_audit_log_entity', 'campaign_ops_audit_log', ['entity_type', 'entity_id'])


def downgrade() -> None:
    """Drop campaign_ops tables."""
    op.drop_table('campaign_ops_audit_log')
    op.drop_table('campaign_ops_metric_entries')
    op.drop_table('campaign_ops_operator_tasks')
    op.drop_table('campaign_ops_calendar_items')
    op.drop_table('campaign_ops_plans')
    op.drop_table('campaign_ops_campaigns')
