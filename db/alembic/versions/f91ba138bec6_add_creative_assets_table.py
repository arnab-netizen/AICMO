"""add_creative_assets_table

Revision ID: f91ba138bec6
Revises: fa9783d90970
Create Date: 2025-12-08 17:45:59.215488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f91ba138bec6'
down_revision: Union[str, Sequence[str], None] = 'fa9783d90970'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'creative_assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('platform', sa.String(), nullable=False),
        sa.Column('format', sa.String(), nullable=False),
        sa.Column('hook', sa.Text(), nullable=False),
        sa.Column('caption', sa.Text(), nullable=True),
        sa.Column('cta', sa.String(), nullable=True),
        sa.Column('tone', sa.String(), nullable=True),
        sa.Column('publish_status', sa.String(), nullable=False, server_default='DRAFT'),
        sa.Column('scheduled_date', sa.String(), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['campaign_id'], ['cam_campaigns.id'])
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('creative_assets')
