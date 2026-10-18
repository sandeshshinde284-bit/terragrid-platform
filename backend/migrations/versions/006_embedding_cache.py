"""Add embedding_cache table

Stores text embeddings so each incident's text is embedded once. The table is
also created at startup by Base.metadata.create_all; this revision creates it
only if it is missing.

Revision ID: 006_embedding_cache
Revises: 005_decision_snapshot
Create Date: 2026-10-18 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006_embedding_cache'
down_revision = '005_decision_snapshot'
branch_labels = None
depends_on = None

TABLE = 'embedding_cache'


def upgrade():
    inspector = sa.inspect(op.get_bind())
    if TABLE in inspector.get_table_names():
        return
    op.create_table(
        TABLE,
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text_hash', sa.String(length=64), nullable=False),
        sa.Column('model_name', sa.String(length=80), nullable=False),
        sa.Column('vector', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('text_hash'),
    )
    op.create_index('ix_embedding_cache_text_hash', TABLE, ['text_hash'])


def downgrade():
    inspector = sa.inspect(op.get_bind())
    if TABLE not in inspector.get_table_names():
        return
    op.drop_index('ix_embedding_cache_text_hash', table_name=TABLE)
    op.drop_table(TABLE)
