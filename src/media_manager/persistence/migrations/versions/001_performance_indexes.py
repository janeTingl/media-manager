"""Add performance indexes and provider cache table.

Revision ID: 001_performance_indexes
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Index


# revision identifiers, used by Alembic.
revision = '001_performance_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add performance indexes and provider cache table."""
    
    # Create provider_cache table
    op.create_table(
        'providercache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('cache_key', sa.String(), nullable=False),
        sa.Column('provider_name', sa.String(), nullable=False),
        sa.Column('query_type', sa.String(), nullable=False),
        sa.Column('query_params', sa.String(), nullable=False),
        sa.Column('response_data', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('hit_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_accessed', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add indexes for provider_cache
    op.create_index('ix_providercache_cache_key', 'providercache', ['cache_key'], unique=True)
    op.create_index('ix_providercache_provider_name', 'providercache', ['provider_name'])
    op.create_index('ix_providercache_query_type', 'providercache', ['query_type'])
    op.create_index('ix_providercache_created_at', 'providercache', ['created_at'])
    op.create_index('ix_providercache_expires_at', 'providercache', ['expires_at'])
    op.create_index('ix_providercache_last_accessed', 'providercache', ['last_accessed'])
    
    # Add composite indexes for common queries on MediaItem
    # Composite index for library + title search
    op.create_index(
        'ix_mediaitem_library_title',
        'mediaitem',
        ['library_id', 'title']
    )
    
    # Composite index for library + year search
    op.create_index(
        'ix_mediaitem_library_year',
        'mediaitem',
        ['library_id', 'year']
    )
    
    # Composite index for library + media_type
    op.create_index(
        'ix_mediaitem_library_type',
        'mediaitem',
        ['library_id', 'media_type']
    )
    
    # Composite index for title + year (for matching)
    op.create_index(
        'ix_mediaitem_title_year',
        'mediaitem',
        ['title', 'year']
    )
    
    # Composite index for season + episode (for TV shows)
    op.create_index(
        'ix_mediaitem_season_episode',
        'mediaitem',
        ['season', 'episode']
    )
    
    # Add composite indexes for person linkage (Credit table)
    # Composite index for media_item + role
    op.create_index(
        'ix_credit_mediaitem_role',
        'credit',
        ['media_item_id', 'role']
    )
    
    # Composite index for person + role (for finding all works by person/role)
    op.create_index(
        'ix_credit_person_role',
        'credit',
        ['person_id', 'role']
    )
    
    # Add indexes for ExternalId lookups
    # Composite index for source + external_id
    op.create_index(
        'ix_externalid_source_external',
        'externalid',
        ['source', 'external_id']
    )
    
    # Add indexes for Artwork queries
    # Composite index for media_item + artwork_type
    op.create_index(
        'ix_artwork_mediaitem_type',
        'artwork',
        ['media_item_id', 'artwork_type']
    )
    
    # Composite index for download_status + artwork_type (for batch operations)
    op.create_index(
        'ix_artwork_status_type',
        'artwork',
        ['download_status', 'artwork_type']
    )
    
    # Add indexes for Subtitle queries
    # Composite index for media_item + language
    op.create_index(
        'ix_subtitle_mediaitem_language',
        'subtitle',
        ['media_item_id', 'language']
    )
    
    # Composite index for download_status + language
    op.create_index(
        'ix_subtitle_status_language',
        'subtitle',
        ['download_status', 'language']
    )
    
    # Add indexes for HistoryEvent queries
    # Composite index for media_item + event_type
    op.create_index(
        'ix_historyevent_mediaitem_type',
        'historyevent',
        ['media_item_id', 'event_type']
    )
    
    # Composite index for event_type + timestamp (for recent activity)
    op.create_index(
        'ix_historyevent_type_timestamp',
        'historyevent',
        ['event_type', 'timestamp']
    )
    
    # Add indexes for JobRun queries
    # Composite index for library + status
    op.create_index(
        'ix_jobrun_library_status',
        'jobrun',
        ['library_id', 'status']
    )
    
    # Composite index for job_type + status
    op.create_index(
        'ix_jobrun_type_status',
        'jobrun',
        ['job_type', 'status']
    )


def downgrade() -> None:
    """Remove performance indexes and provider cache table."""
    
    # Drop JobRun indexes
    op.drop_index('ix_jobrun_type_status', 'jobrun')
    op.drop_index('ix_jobrun_library_status', 'jobrun')
    
    # Drop HistoryEvent indexes
    op.drop_index('ix_historyevent_type_timestamp', 'historyevent')
    op.drop_index('ix_historyevent_mediaitem_type', 'historyevent')
    
    # Drop Subtitle indexes
    op.drop_index('ix_subtitle_status_language', 'subtitle')
    op.drop_index('ix_subtitle_mediaitem_language', 'subtitle')
    
    # Drop Artwork indexes
    op.drop_index('ix_artwork_status_type', 'artwork')
    op.drop_index('ix_artwork_mediaitem_type', 'artwork')
    
    # Drop ExternalId indexes
    op.drop_index('ix_externalid_source_external', 'externalid')
    
    # Drop Credit indexes
    op.drop_index('ix_credit_person_role', 'credit')
    op.drop_index('ix_credit_mediaitem_role', 'credit')
    
    # Drop MediaItem indexes
    op.drop_index('ix_mediaitem_season_episode', 'mediaitem')
    op.drop_index('ix_mediaitem_title_year', 'mediaitem')
    op.drop_index('ix_mediaitem_library_type', 'mediaitem')
    op.drop_index('ix_mediaitem_library_year', 'mediaitem')
    op.drop_index('ix_mediaitem_library_title', 'mediaitem')
    
    # Drop provider_cache indexes
    op.drop_index('ix_providercache_last_accessed', 'providercache')
    op.drop_index('ix_providercache_expires_at', 'providercache')
    op.drop_index('ix_providercache_created_at', 'providercache')
    op.drop_index('ix_providercache_query_type', 'providercache')
    op.drop_index('ix_providercache_provider_name', 'providercache')
    op.drop_index('ix_providercache_cache_key', 'providercache')
    
    # Drop provider_cache table
    op.drop_table('providercache')
