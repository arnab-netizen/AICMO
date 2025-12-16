"""add audit log

Revision ID: add_audit_log
Revises: add_distribution
Create Date: 2025-12-14 17:50:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_audit_log'
down_revision: Union[str, None] = 'add_distribution'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create audit_log table
    op.create_table('audit_log',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('entity_type', sa.String(), nullable=False),
    sa.Column('entity_id', sa.String(), nullable=False),
    sa.Column('action', sa.String(), nullable=False),
    sa.Column('actor', sa.String(), nullable=False),
    sa.Column('context', sa.JSON(), nullable=True),
    sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Indexes for querying
    op.create_index('idx_audit_entity', 'audit_log', ['entity_type', 'entity_id'], unique=False)
    op.create_index('idx_audit_action', 'audit_log', ['action'], unique=False)
    op.create_index('idx_audit_timestamp', 'audit_log', ['timestamp'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_audit_timestamp', table_name='audit_log')
    op.drop_index('idx_audit_action', table_name='audit_log')
    op.drop_index('idx_audit_entity', table_name='audit_log')
    op.drop_table('audit_log')
