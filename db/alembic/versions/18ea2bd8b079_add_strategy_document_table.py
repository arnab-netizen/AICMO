"""add_strategy_document_table

Revision ID: 18ea2bd8b079
Revises: 1a63c14e2e8a
Create Date: 2025-12-13 11:45:18.129564

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '18ea2bd8b079'
down_revision: Union[str, Sequence[str], None] = '1a63c14e2e8a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create strategy_document table
    op.create_table(
        'strategy_document',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('brief_id', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('kpis', sa.JSON(), nullable=False),
        sa.Column('channels', sa.JSON(), nullable=False),
        sa.Column('timeline', sa.JSON(), nullable=False),
        sa.Column('executive_summary', sa.Text(), nullable=False),
        sa.Column('is_approved', sa.Boolean(), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('brief_id', 'version', name='uq_strategy_brief_version')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('strategy_document')
