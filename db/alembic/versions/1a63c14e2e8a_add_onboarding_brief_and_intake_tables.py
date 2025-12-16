"""add_onboarding_brief_and_intake_tables

Revision ID: 1a63c14e2e8a
Revises: 7d9e4a2b1c3f
Create Date: 2025-12-13 11:31:45.242460

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1a63c14e2e8a'
down_revision: Union[str, Sequence[str], None] = '7d9e4a2b1c3f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create onboarding_brief table
    op.create_table(
        'onboarding_brief',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('deliverables', sa.JSON(), nullable=False),
        sa.Column('exclusions', sa.JSON(), nullable=False),
        sa.Column('timeline_weeks', sa.String(), nullable=True),
        sa.Column('objectives', sa.JSON(), nullable=False),
        sa.Column('target_audience', sa.Text(), nullable=False),
        sa.Column('brand_guidelines', sa.JSON(), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('normalized_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create onboarding_intake table
    op.create_table(
        'onboarding_intake',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('brief_id', sa.String(), nullable=True),
        sa.Column('client_id', sa.String(), nullable=False),
        sa.Column('responses', sa.JSON(), nullable=False),
        sa.Column('attachments', sa.JSON(), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('onboarding_intake')
    op.drop_table('onboarding_brief')
