"""add cam safety settings

Revision ID: 5e3a9d7f2b4c
Revises: 4d2f8a9b1e3c
Create Date: 2025-12-08 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e3a9d7f2b4c'
down_revision = '4d2f8a9b1e3c'
branch_labels = None
depends_on = None


def upgrade():
    # Create cam_safety_settings table
    op.create_table(
        'cam_safety_settings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('cam_safety_settings')
