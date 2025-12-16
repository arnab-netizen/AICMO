"""add_all_phase_fields_to_leads

Revision ID: 71751d732ad2
Revises: add_audit_log
Create Date: 2025-12-14 19:15:08.790263

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '71751d732ad2'
down_revision: Union[str, Sequence[str], None] = 'add_audit_log'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add Phase 6, Phase A, Phase B, and Phase D fields to cam_leads.
    Phase 5 fields (routing_sequence, sequence_start_at, engagement_notes) already exist."""
    
    # Phase 6: Lead Nurture (skipping engagement_notes - already exists)
    op.add_column('cam_leads', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('title', sa.String(), nullable=True))
    
    # Phase A: CRM Fields - Company Information
    op.add_column('cam_leads', sa.Column('company_size', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('industry', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('growth_rate', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('annual_revenue', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('employee_count', sa.Integer(), nullable=True))
    op.add_column('cam_leads', sa.Column('company_website', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('company_headquarters', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('founding_year', sa.Integer(), nullable=True))
    op.add_column('cam_leads', sa.Column('funding_status', sa.String(), nullable=True))
    
    # Phase A: CRM Fields - Decision Maker
    op.add_column('cam_leads', sa.Column('decision_maker_name', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('decision_maker_email', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('decision_maker_role', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('decision_maker_linkedin', sa.String(), nullable=True))
    
    # Phase A: CRM Fields - Sales Information
    op.add_column('cam_leads', sa.Column('budget_estimate_range', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('timeline_months', sa.Integer(), nullable=True))
    op.add_column('cam_leads', sa.Column('pain_points', postgresql.JSON(), nullable=True))
    op.add_column('cam_leads', sa.Column('buying_signals', postgresql.JSON(), nullable=True))
    
    # Phase A: CRM Fields - Lead Grading
    op.add_column('cam_leads', sa.Column('lead_grade', sa.String(), nullable=True, server_default='D'))
    op.add_column('cam_leads', sa.Column('conversion_probability', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('cam_leads', sa.Column('fit_score_for_service', sa.Float(), nullable=True, server_default='0.0'))
    op.add_column('cam_leads', sa.Column('graded_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cam_leads', sa.Column('grade_reason', sa.String(), nullable=True))
    
    # Phase A: CRM Fields - Tracking
    op.add_column('cam_leads', sa.Column('proposal_generated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cam_leads', sa.Column('proposal_content_id', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('contract_signed_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cam_leads', sa.Column('referral_source', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('referred_by_name', sa.String(), nullable=True))
    
    # Phase B: Outreach Channels
    op.add_column('cam_leads', sa.Column('linkedin_status', sa.String(), nullable=True, server_default='not_connected'))
    op.add_column('cam_leads', sa.Column('contact_form_url', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('contact_form_last_submitted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Phase D: Lead Acquisition System
    op.add_column('cam_leads', sa.Column('qualification_notes', sa.Text(), nullable=True))
    op.add_column('cam_leads', sa.Column('email_valid', sa.Boolean(), nullable=True))
    op.add_column('cam_leads', sa.Column('intent_signals', postgresql.JSON(), nullable=True))
    
    # Create indexes for grading fields
    op.create_index('idx_lead_grade', 'cam_leads', ['lead_grade'])
    op.create_index('idx_conversion_probability', 'cam_leads', ['conversion_probability'])
    op.create_index('idx_fit_score_for_service', 'cam_leads', ['fit_score_for_service'])


def downgrade() -> None:
    """Remove Phase 5, Phase 6, Phase A, Phase B, and Phase D fields from cam_leads."""
    # Drop indexes first
    op.drop_index('idx_fit_score_for_service', 'cam_leads')
    op.drop_index('idx_conversion_probability', 'cam_leads')
    op.drop_index('idx_lead_grade', 'cam_leads')
    
    # Phase D
    op.drop_column('cam_leads', 'intent_signals')
    op.drop_column('cam_leads', 'email_valid')
    op.drop_column('cam_leads', 'qualification_notes')
    
    # Phase B
    op.drop_column('cam_leads', 'contact_form_last_submitted_at')
    op.drop_column('cam_leads', 'contact_form_url')
    op.drop_column('cam_leads', 'linkedin_status')
    
    # Phase A: Tracking
    op.drop_column('cam_leads', 'referred_by_name')
    op.drop_column('cam_leads', 'referral_source')
    op.drop_column('cam_leads', 'contract_signed_at')
    op.drop_column('cam_leads', 'proposal_content_id')
    op.drop_column('cam_leads', 'proposal_generated_at')
    
    # Phase A: Lead Grading
    op.drop_column('cam_leads', 'grade_reason')
    op.drop_column('cam_leads', 'graded_at')
    op.drop_column('cam_leads', 'fit_score_for_service')
    op.drop_column('cam_leads', 'conversion_probability')
    op.drop_column('cam_leads', 'lead_grade')
    
    # Phase A: Sales Information
    op.drop_column('cam_leads', 'buying_signals')
    op.drop_column('cam_leads', 'pain_points')
    op.drop_column('cam_leads', 'timeline_months')
    op.drop_column('cam_leads', 'budget_estimate_range')
    
    # Phase A: Decision Maker
    op.drop_column('cam_leads', 'decision_maker_linkedin')
    op.drop_column('cam_leads', 'decision_maker_role')
    op.drop_column('cam_leads', 'decision_maker_email')
    op.drop_column('cam_leads', 'decision_maker_name')
    
    # Phase A: Company Information
    op.drop_column('cam_leads', 'funding_status')
    op.drop_column('cam_leads', 'founding_year')
    op.drop_column('cam_leads', 'company_headquarters')
    op.drop_column('cam_leads', 'company_website')
    op.drop_column('cam_leads', 'employee_count')
    op.drop_column('cam_leads', 'annual_revenue')
    op.drop_column('cam_leads', 'growth_rate')
    op.drop_column('cam_leads', 'industry')
    op.drop_column('cam_leads', 'company_size')
    
    # Phase 6
    op.drop_column('cam_leads', 'title')
    op.drop_column('cam_leads', 'first_name')
    op.drop_column('cam_leads', 'engagement_notes')
    
    # Phase 5
    op.drop_column('cam_leads', 'sequence_start_at')
    op.drop_column('cam_leads', 'routing_sequence')

