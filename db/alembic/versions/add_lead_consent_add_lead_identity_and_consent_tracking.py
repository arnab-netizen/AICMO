"""add lead identity and consent tracking

Revision ID: add_lead_consent
Revises: add_venture_config
Create Date: 2025-12-14 17:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_lead_consent'
down_revision: Union[str, None] = 'add_venture_config'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add identity resolution and consent tracking to LeadDB
    op.add_column('cam_leads', sa.Column('venture_id', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('identity_hash', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('consent_status', sa.String(), nullable=False, server_default='UNKNOWN'))
    op.add_column('cam_leads', sa.Column('consent_date', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cam_leads', sa.Column('source_channel', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('source_ref', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('utm_campaign', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('utm_content', sa.String(), nullable=True))
    op.add_column('cam_leads', sa.Column('first_touch_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cam_leads', sa.Column('last_touch_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('cam_leads', sa.Column('value_estimate', sa.Float(), nullable=True))
    
    # Create indexes for deduplication and consent checks
    op.create_index('idx_identity_hash', 'cam_leads', ['identity_hash'], unique=False)
    op.create_index('idx_consent_status', 'cam_leads', ['consent_status'], unique=False)
    op.create_index('idx_venture_campaign', 'cam_leads', ['venture_id', 'campaign_id'], unique=False)
    
    # Add foreign key to ventures
    op.create_foreign_key('fk_lead_venture', 'cam_leads', 'ventures', ['venture_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_lead_venture', 'cam_leads', type_='foreignkey')
    op.drop_index('idx_venture_campaign', table_name='cam_leads')
    op.drop_index('idx_consent_status', table_name='cam_leads')
    op.drop_index('idx_identity_hash', table_name='cam_leads')
    op.drop_column('cam_leads', 'value_estimate')
    op.drop_column('cam_leads', 'last_touch_at')
    op.drop_column('cam_leads', 'first_touch_at')
    op.drop_column('cam_leads', 'utm_content')
    op.drop_column('cam_leads', 'utm_campaign')
    op.drop_column('cam_leads', 'source_ref')
    op.drop_column('cam_leads', 'source_channel')
    op.drop_column('cam_leads', 'consent_date')
    op.drop_column('cam_leads', 'consent_status')
    op.drop_column('cam_leads', 'identity_hash')
    op.drop_column('cam_leads', 'venture_id')
