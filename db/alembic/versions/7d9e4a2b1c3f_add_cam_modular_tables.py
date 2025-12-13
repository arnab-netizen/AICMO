"""Add CAM modular architecture tables.

Revision ID: 7d9e4a2b1c3f
Revises: 5f6a8c9d0e1f
Create Date: 2025-12-12 20:30:00.000000

Tables added:
- cam_outbound_emails: Tracks outbound emails with idempotency
- cam_inbound_emails: Tracks inbound replies with threading
- cam_worker_heartbeats: Worker health and locking
- cam_human_alert_logs: Alert audit trail and idempotency
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7d9e4a2b1c3f'
down_revision = '5f6a8c9d0e1f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create CAM modular architecture tables."""
    
    # cam_outbound_emails table
    op.create_table(
        'cam_outbound_emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('to_email', sa.String(), nullable=False),
        sa.Column('from_email', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('html_body', sa.Text(), nullable=True),
        sa.Column('content_hash', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_message_id', sa.String(), nullable=True),
        sa.Column('message_id_header', sa.String(), nullable=True),
        sa.Column('sequence_number', sa.Integer(), nullable=True),
        sa.Column('campaign_sequence_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='QUEUED'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('max_retries', sa.Integer(), nullable=False, server_default='3'),
        sa.Column('next_retry_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('queued_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('bounced_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['cam_campaigns.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['cam_leads.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('provider_message_id'),
        sa.UniqueConstraint('message_id_header'),
    )
    op.create_index('idx_outbound_email_campaign', 'cam_outbound_emails', ['campaign_id'])
    op.create_index('idx_outbound_email_lead', 'cam_outbound_emails', ['lead_id'])
    op.create_index('idx_outbound_email_provider_msg_id', 'cam_outbound_emails', ['provider_message_id'])
    op.create_index('idx_outbound_email_sent_at', 'cam_outbound_emails', ['sent_at'])
    op.create_index('idx_outbound_email_status', 'cam_outbound_emails', ['status'])
    
    # cam_inbound_emails table
    op.create_table(
        'cam_inbound_emails',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('provider_msg_uid', sa.String(), nullable=False),
        sa.Column('from_email', sa.String(), nullable=False),
        sa.Column('to_email', sa.String(), nullable=True),
        sa.Column('subject', sa.String(), nullable=True),
        sa.Column('in_reply_to_message_id', sa.String(), nullable=True),
        sa.Column('in_reply_to_outbound_email_id', sa.Integer(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('classification', sa.String(), nullable=True),
        sa.Column('classification_confidence', sa.Float(), nullable=True, server_default='0.0'),
        sa.Column('classification_reason', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('ingested_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('email_metadata', sa.JSON(), nullable=True, server_default='{}'),
        sa.Column('alert_sent', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['cam_campaigns.id'], ),
        sa.ForeignKeyConstraint(['in_reply_to_outbound_email_id'], ['cam_outbound_emails.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['cam_leads.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('idx_inbound_email_campaign', 'cam_inbound_emails', ['campaign_id'])
    op.create_index('idx_inbound_email_classification', 'cam_inbound_emails', ['classification'])
    op.create_index('idx_inbound_email_from', 'cam_inbound_emails', ['from_email'])
    op.create_index('idx_inbound_email_lead', 'cam_inbound_emails', ['lead_id'])
    op.create_index('idx_inbound_email_provider_uid', 'cam_inbound_emails', ['provider', 'provider_msg_uid'])
    op.create_index('idx_inbound_email_received_at', 'cam_inbound_emails', ['received_at'])
    
    # cam_worker_heartbeats table
    op.create_table(
        'cam_worker_heartbeats',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, server_default='RUNNING'),
        sa.Column('last_seen_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('worker_id'),
    )
    op.create_index('idx_worker_heartbeat_last_seen', 'cam_worker_heartbeats', ['last_seen_at'])
    op.create_index('idx_worker_heartbeat_status', 'cam_worker_heartbeats', ['status'])
    
    # cam_human_alert_logs table
    op.create_table(
        'cam_human_alert_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=True),
        sa.Column('campaign_id', sa.Integer(), nullable=True),
        sa.Column('inbound_email_id', sa.Integer(), nullable=True),
        sa.Column('recipients', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('sent_successfully', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('idempotency_key', sa.String(), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['campaign_id'], ['cam_campaigns.id'], ),
        sa.ForeignKeyConstraint(['lead_id'], ['cam_leads.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('idempotency_key'),
    )
    op.create_index('idx_alert_log_campaign', 'cam_human_alert_logs', ['campaign_id'])
    op.create_index('idx_alert_log_idempotency', 'cam_human_alert_logs', ['idempotency_key'])
    op.create_index('idx_alert_log_lead', 'cam_human_alert_logs', ['lead_id'])
    op.create_index('idx_alert_log_sent_at', 'cam_human_alert_logs', ['sent_at'])
    op.create_index('idx_alert_log_type', 'cam_human_alert_logs', ['alert_type'])


def downgrade() -> None:
    """Drop CAM modular architecture tables."""
    
    # Drop tables in reverse order (respecting FK constraints)
    op.drop_table('cam_human_alert_logs')
    op.drop_table('cam_worker_heartbeats')
    op.drop_table('cam_inbound_emails')
    op.drop_table('cam_outbound_emails')
