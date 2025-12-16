"""add_production_draft_bundle_tables

Revision ID: 8dc2194a008b
Revises: 18ea2bd8b079
Create Date: 2025-12-13 12:15:03.911142

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8dc2194a008b'
down_revision: Union[str, Sequence[str], None] = '18ea2bd8b079'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add Production module tables for ports-aligned persistence.
    
    Tables:
    - production_drafts: ContentDraft entities (draft_id idempotency key)
    - production_bundles: DraftBundle entities (bundle_id idempotency key)
    - production_bundle_assets: BundleAsset entities (asset_id idempotency key)
    
    Note: Existing production_assets table (legacy Stage 2) is NOT touched.
    """
    # production_drafts table
    op.create_table(
        'production_drafts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('draft_id', sa.String(), nullable=False),
        sa.Column('strategy_id', sa.String(), nullable=False),
        sa.Column('content_type', sa.String(), nullable=False),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('draft_id', name='uq_production_drafts_draft_id'),
    )
    op.create_index(
        'ix_production_drafts_strategy_id',
        'production_drafts',
        ['strategy_id'],
        unique=False,
    )
    
    # production_bundles table
    op.create_table(
        'production_bundles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('bundle_id', sa.String(), nullable=False),
        sa.Column('draft_id', sa.String(), nullable=False),
        sa.Column('assembled_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('bundle_id', name='uq_production_bundles_bundle_id'),
    )
    op.create_index(
        'ix_production_bundles_draft_id',
        'production_bundles',
        ['draft_id'],
        unique=False,
    )
    
    # production_bundle_assets table
    op.create_table(
        'production_bundle_assets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.String(), nullable=False),
        sa.Column('bundle_id', sa.String(), nullable=False),
        sa.Column('asset_type', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('meta', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id', name='uq_production_bundle_assets_asset_id'),
    )
    op.create_index(
        'ix_production_bundle_assets_bundle_id',
        'production_bundle_assets',
        ['bundle_id'],
        unique=False,
    )


def downgrade() -> None:
    """
    Remove Production module tables.
    
    Drops tables in reverse order (assets → bundles → drafts).
    """
    op.drop_index('ix_production_bundle_assets_bundle_id', table_name='production_bundle_assets')
    op.drop_table('production_bundle_assets')
    
    op.drop_index('ix_production_bundles_draft_id', table_name='production_bundles')
    op.drop_table('production_bundles')
    
    op.drop_index('ix_production_drafts_strategy_id', table_name='production_drafts')
    op.drop_table('production_drafts')
