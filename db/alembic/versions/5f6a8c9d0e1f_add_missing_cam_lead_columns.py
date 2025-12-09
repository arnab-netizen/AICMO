"""add missing CAM lead columns

This migration adds missing columns to cam_leads table that were defined
in the ORM model but not created by initial migrations.

Missing columns being added:
- lead_score: Lead quality/fit score (0.0-1.0)
- tags: JSON array of lead tags (hot, warm, cold, etc.)
- enrichment_data: JSON with enriched contact information
- last_contacted_at: Timestamp of last contact attempt
- next_action_at: Scheduled time for next contact
- last_replied_at: Timestamp of last reply from lead
- requires_human_review: Flag indicating need for manual intervention
- review_type: Type of human review needed (MESSAGE, PROPOSAL, PRICING)
- review_reason: Reason for human review requirement

Revision ID: 5f6a8c9d0e1f
Revises: 4d2f8a9b1e3c
Create Date: 2025-12-09 11:25:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '5f6a8c9d0e1f'
down_revision = ('4d2f8a9b1e3c', '6c7f03514563')  # Multiple parents to merge branches
branch_labels = None
depends_on = None


def upgrade():
    """Add missing columns to cam_leads table."""
    with op.batch_alter_table('cam_leads', schema=None) as batch_op:
        # Lead scoring and profiling
        batch_op.add_column(
            sa.Column('lead_score', sa.Float(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('tags', sa.JSON(), nullable=False, server_default='[]')
        )
        batch_op.add_column(
            sa.Column('enrichment_data', sa.JSON(), nullable=True)
        )
        
        # Timing and follow-up
        batch_op.add_column(
            sa.Column('last_contacted_at', sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column('next_action_at', sa.DateTime(timezone=True), nullable=True)
        )
        batch_op.add_column(
            sa.Column('last_replied_at', sa.DateTime(timezone=True), nullable=True)
        )
        
        # Human review queue
        batch_op.add_column(
            sa.Column('requires_human_review', sa.Boolean(), nullable=False, server_default='false')
        )
        batch_op.add_column(
            sa.Column('review_type', sa.String(), nullable=True)
        )
        batch_op.add_column(
            sa.Column('review_reason', sa.Text(), nullable=True)
        )


def downgrade():
    """Remove added columns from cam_leads table."""
    with op.batch_alter_table('cam_leads', schema=None) as batch_op:
        batch_op.drop_column('review_reason')
        batch_op.drop_column('review_type')
        batch_op.drop_column('requires_human_review')
        batch_op.drop_column('last_replied_at')
        batch_op.drop_column('next_action_at')
        batch_op.drop_column('last_contacted_at')
        batch_op.drop_column('enrichment_data')
        batch_op.drop_column('tags')
        batch_op.drop_column('lead_score')
