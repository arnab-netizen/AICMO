"""add_qc_tables

Revision ID: a62ac144b3d7
Revises: 8dc2194a008b
Create Date: 2025-12-13 13:34:57.765668

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a62ac144b3d7'
down_revision: Union[str, Sequence[str], None] = '8dc2194a008b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - Add QC persistence tables."""
    # Create qc_results table
    op.create_table(
        'qc_results',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('draft_id', sa.String(), nullable=False),
        sa.Column('passed', sa.Boolean(), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('draft_id', name='uq_qc_result_draft_id'),
    )
    op.create_index('ix_qc_results_draft_id', 'qc_results', ['draft_id'])
    
    # Create qc_issues table
    op.create_table(
        'qc_issues',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('result_id', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('section', sa.String(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['result_id'], ['qc_results.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_qc_issues_result_id', 'qc_issues', ['result_id'])


def downgrade() -> None:
    """Downgrade schema - Remove QC tables."""
    op.drop_index('ix_qc_issues_result_id', table_name='qc_issues')
    op.drop_table('qc_issues')
    op.drop_index('ix_qc_results_draft_id', table_name='qc_results')
    op.drop_table('qc_results')
