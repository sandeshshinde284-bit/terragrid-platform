"""Add 4-Layer Lineage tables for Source of Truth feature

Revision ID: 003_add_lineage_tables
Revises: 002_increase_location_name
Create Date: 2026-10-11 13:56:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '003_add_lineage_tables'
down_revision = '002_increase_location_name'
branch_labels = None
depends_on = None


def upgrade():
    # Create raw_events table (Layer 1: Raw Ingestion)
    op.create_table(
        'raw_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('api_response', JSONB(), nullable=False),
        sa.Column('http_status_code', sa.Integer(), nullable=False),
        sa.Column('fetched_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_raw_events_source', 'raw_events', ['source'])
    op.create_index('ix_raw_events_created_at', 'raw_events', ['created_at'])
    
    # Create validation_log table (Layer 2: Validation)
    op.create_table(
        'validation_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_event_id', sa.Integer(), nullable=False),
        sa.Column('validation_status', sa.String(20), nullable=False),
        sa.Column('errors', JSONB(), nullable=True),
        sa.Column('validator_version', sa.String(20), nullable=False),
        sa.Column('validated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['raw_event_id'], ['raw_events.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_validation_raw_event', 'validation_log', ['raw_event_id'])
    op.create_index('ix_validation_status', 'validation_log', ['validation_status'])
    
    # Create enrichment_log table (Layer 3: Enrichment)
    op.create_table(
        'enrichment_log',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('validation_log_id', sa.Integer(), nullable=False),
        sa.Column('enrichment_type', sa.String(50), nullable=False),
        sa.Column('enrichment_service', sa.String(50), nullable=False),
        sa.Column('original_value', JSONB(), nullable=True),
        sa.Column('enriched_value', JSONB(), nullable=False),
        sa.Column('enriched_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['validation_log_id'], ['validation_log.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_enrichment_validation', 'enrichment_log', ['validation_log_id'])
    op.create_index('ix_enrichment_type', 'enrichment_log', ['enrichment_type'])
    
    # Create lineage_chain table (Glue: Links all 4 layers)
    op.create_table(
        'lineage_chain',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('raw_event_id', sa.Integer(), nullable=False),
        sa.Column('validation_log_id', sa.Integer(), nullable=False),
        sa.Column('enrichment_log_id', sa.Integer(), nullable=False),
        sa.Column('final_event_id', sa.Integer(), nullable=False),
        sa.Column('processing_status', sa.String(20), nullable=False),
        sa.Column('total_processing_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['raw_event_id'], ['raw_events.id']),
        sa.ForeignKeyConstraint(['validation_log_id'], ['validation_log.id']),
        sa.ForeignKeyConstraint(['enrichment_log_id'], ['enrichment_log.id']),
        sa.ForeignKeyConstraint(['final_event_id'], ['events.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_lineage_final_event', 'lineage_chain', ['final_event_id'])
    op.create_index('ix_lineage_raw_event', 'lineage_chain', ['raw_event_id'])
    op.create_index('ix_lineage_processing_status', 'lineage_chain', ['processing_status'])


def downgrade():
    # Drop lineage_chain table
    op.drop_index('ix_lineage_processing_status')
    op.drop_index('ix_lineage_raw_event')
    op.drop_index('ix_lineage_final_event')
    op.drop_table('lineage_chain')
    
    # Drop enrichment_log table
    op.drop_index('ix_enrichment_type')
    op.drop_index('ix_enrichment_validation')
    op.drop_table('enrichment_log')
    
    # Drop validation_log table
    op.drop_index('ix_validation_status')
    op.drop_index('ix_validation_raw_event')
    op.drop_table('validation_log')
    
    # Drop raw_events table
    op.drop_index('ix_raw_events_created_at')
    op.drop_index('ix_raw_events_source')
    op.drop_table('raw_events')
