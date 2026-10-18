"""Make event_id nullable in incident_preparedness_contexts (Phase 2)

Allow saving preparedness assessments without linking to an incident for later linking.

Revision ID: 009_nullable_event_id
Revises: 008_preparedness_context
Create Date: 2026-10-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '009_nullable_event_id'
down_revision = '008_preparedness_context'
branch_labels = None
depends_on = None

TABLE = 'incident_preparedness_contexts'


def upgrade():
    """Make event_id nullable to support unlinked assessments."""
    inspector = sa.inspect(op.get_bind())
    if TABLE not in inspector.get_table_names():
        return

    # Alter event_id column to be nullable
    # PostgreSQL: use ALTER COLUMN ... DROP NOT NULL
    op.alter_column(
        TABLE,
        'event_id',
        existing_type=sa.Integer(),
        nullable=True,
    )


def downgrade():
    """Revert: make event_id NOT NULL (requires all rows to have event_id)."""
    inspector = sa.inspect(op.get_bind())
    if TABLE not in inspector.get_table_names():
        return

    # Before making NOT NULL, ensure no NULLs exist
    # (This could fail if unlinked assessments were saved)
    op.alter_column(
        TABLE,
        'event_id',
        existing_type=sa.Integer(),
        nullable=False,
    )
