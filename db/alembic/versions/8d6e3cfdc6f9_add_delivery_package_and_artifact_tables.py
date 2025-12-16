"""add_delivery_package_and_artifact_tables

Revision ID: 8d6e3cfdc6f9
Revises: a62ac144b3d7
Create Date: 2025-12-13 14:14:25.716156

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '8d6e3cfdc6f9'
down_revision: Union[str, Sequence[str], None] = 'a62ac144b3d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create delivery_packages table
    op.create_table(
        'delivery_packages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('package_id', sa.String(), nullable=False),
        sa.Column('draft_id', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('package_id')
    )
    op.create_index('ix_delivery_packages_package_id', 'delivery_packages', ['package_id'], unique=False)
    op.create_index('ix_delivery_packages_draft_id', 'delivery_packages', ['draft_id'], unique=False)
    
    # Create delivery_artifacts table
    op.create_table(
        'delivery_artifacts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('package_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('format', sa.String(), nullable=False),
        sa.Column('position', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_delivery_artifacts_package_id', 'delivery_artifacts', ['package_id'], unique=False)
    op.create_index('ix_delivery_artifacts_package_id_position', 'delivery_artifacts', ['package_id', 'position'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_delivery_artifacts_package_id_position', table_name='delivery_artifacts')
    op.drop_index('ix_delivery_artifacts_package_id', table_name='delivery_artifacts')
    op.drop_table('delivery_artifacts')
    op.drop_index('ix_delivery_packages_draft_id', table_name='delivery_packages')
    op.drop_index('ix_delivery_packages_package_id', table_name='delivery_packages')
    op.drop_table('delivery_packages')
