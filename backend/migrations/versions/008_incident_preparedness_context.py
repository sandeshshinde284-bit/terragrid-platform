"""Add incident_preparedness_contexts table

Snapshot of preparedness assessment linked to an incident.
Stores city, hazard, risk, assessment time, and checklist snapshot.

Revision ID: 008_incident_preparedness_context
Revises: 007_response_plan_details
Create Date: 2026-10-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '008_incident_preparedness_context'
down_revision = '007_response_plan_details'
branch_labels = None
depends_on = None

TABLE = 'incident_preparedness_contexts'


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if TABLE in inspector.get_table_names():
        return
    op.create_table(
        TABLE,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('city', sa.String(length=120), nullable=False),
        sa.Column('country', sa.String(length=120), nullable=False),
        sa.Column('hazard_type', sa.String(length=50), nullable=True),
        sa.Column('risk_level', sa.String(length=20), nullable=True),
        sa.Column('assessment_at', sa.DateTime(), nullable=False),
        sa.Column('snapshot_json', JSONB(), nullable=True),
        sa.Column('source_metadata_json', JSONB(), nullable=True),
        sa.Column('initiated_by', sa.String(length=120), nullable=False),
        sa.Column('compatibility_override_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['event_id'], ['events.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_incident_preparedness_contexts_event_id', TABLE, ['event_id'])


def downgrade():
    inspector = sa.inspect(op.get_bind())
    if TABLE not in inspector.get_table_names():
        return
    op.drop_index('ix_incident_preparedness_contexts_event_id', table_name=TABLE)
    op.drop_table(TABLE)
