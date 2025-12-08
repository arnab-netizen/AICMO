"""add cam pipeline tables

Revision ID: 4d2f8a9b1e3c
Revises: 3b1561457c07
Create Date: 2025-12-08 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d2f8a9b1e3c'
down_revision = '3b1561457c07'
branch_labels = None
depends_on = None


def upgrade():
    # Add stage column to cam_leads
    with op.batch_alter_table('cam_leads', schema=None) as batch_op:
        batch_op.add_column(sa.Column('stage', sa.String(), nullable=False, server_default='NEW'))

    # Create cam_contact_events table
    op.create_table(
        'cam_contact_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('direction', sa.String(), nullable=False),
        sa.Column('summary', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['cam_leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create cam_appointments table
    op.create_table(
        'cam_appointments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('lead_id', sa.Integer(), nullable=False),
        sa.Column('scheduled_for', sa.DateTime(timezone=True), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False, server_default='30'),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('calendar_link', sa.String(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='SCHEDULED'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['cam_leads.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('cam_appointments')
    op.drop_table('cam_contact_events')
    
    with op.batch_alter_table('cam_leads', schema=None) as batch_op:
        batch_op.drop_column('stage')
