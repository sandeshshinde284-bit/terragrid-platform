"""Increase location_name field size from VARCHAR(255) to TEXT

Revision ID: 002_increase_location_name
Revises: 5186b3167b41
Create Date: 2026-10-04 12:37:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_increase_location_name'
down_revision = '5186b3167b41'
branch_labels = None
depends_on = None


def upgrade():
    # Alter the location_name column to use TEXT instead of VARCHAR(255)
    # This allows NOAA weather alerts with very long location descriptions
    op.alter_column('events', 'location_name',
                    existing_type=sa.String(255),
                    type_=sa.Text(),
                    existing_nullable=True,
                    nullable=True)


def downgrade():
    # Revert to VARCHAR(255)
    op.alter_column('events', 'location_name',
                    existing_type=sa.Text(),
                    type_=sa.String(255),
                    existing_nullable=True,
                    nullable=True)
