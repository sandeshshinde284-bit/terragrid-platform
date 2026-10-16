"""Add alert_recipients table (Settings-managed Agency Alerts recipients)

Replaces the WHATSAPP_RECIPIENTS / EMAIL_ALERT_RECIPIENTS env vars with a
DB table editable from the Settings screen at runtime - no Cloud Run
redeploy needed to add/remove a demo recipient.

Revision ID: 004_add_alert_recipients
Revises: 003_add_lineage_tables
Create Date: 2026-10-15 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004_add_alert_recipients'
down_revision = '003_add_lineage_tables'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'alert_recipients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('channel', sa.String(length=20), nullable=False),
        sa.Column('label', sa.String(length=100), nullable=False),
        sa.Column('value', sa.String(length=255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_alert_recipients_channel', 'alert_recipients', ['channel'])


def downgrade():
    op.drop_index('ix_alert_recipients_channel', table_name='alert_recipients')
    op.drop_table('alert_recipients')
