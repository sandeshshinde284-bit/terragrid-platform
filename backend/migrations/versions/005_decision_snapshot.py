"""Snapshot AI priority/category and officer priority on response plan decisions

The response tables are created at startup by Base.metadata.create_all, not by
these migrations. So this revision adds the new columns only where the table
already exists and the column is missing. On a fresh database the table is
created by create_all with the columns already in the model.

Revision ID: 005_response_plan_decision_snapshot
Revises: 004_add_alert_recipients
Create Date: 2026-10-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005_decision_snapshot'
down_revision = '004_add_alert_recipients'
branch_labels = None
depends_on = None

TABLE = 'response_plan_decisions'
NEW_COLUMNS = [
    ('ai_priority', sa.String(length=12)),
    ('ai_category', sa.String(length=40)),
    ('officer_priority', sa.String(length=10)),
]


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if TABLE not in inspector.get_table_names():
        return  # created by create_all with these columns
    existing = {c['name'] for c in inspector.get_columns(TABLE)}
    for name, column_type in NEW_COLUMNS:
        if name not in existing:
            op.add_column(TABLE, sa.Column(name, column_type, nullable=True))


def downgrade():
    inspector = sa.inspect(op.get_bind())
    if TABLE not in inspector.get_table_names():
        return
    existing = {c['name'] for c in inspector.get_columns(TABLE)}
    for name, _ in NEW_COLUMNS:
        if name in existing:
            op.drop_column(TABLE, name)
