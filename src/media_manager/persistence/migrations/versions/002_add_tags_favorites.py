"""Add tags, favorites, and collections tables and indexes.

Revision ID: 002_add_tags_favorites
Revises: 001_performance_indexes
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import Index


# revision identifiers, used by Alembic.
revision = '002_add_tags_favorites'
down_revision = '001_performance_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add tags, favorites, and collections tables."""
    
    # Create tag table
    op.create_table(
        'tag',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('color', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_tag_name', 'tag', ['name'], unique=True)
    
    # Create mediaitemtag association table
    op.create_table(
        'mediaitemtag',
        sa.Column('media_item_id', sa.Integer(), nullable=True),
        sa.Column('tag_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['media_item_id'], ['mediaitem.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tag.id'], ),
        sa.PrimaryKeyConstraint('media_item_id', 'tag_id')
    )
    op.create_index('ix_mediaitemtag_media_item_id', 'mediaitemtag', ['media_item_id'])
    op.create_index('ix_mediaitemtag_tag_id', 'mediaitemtag', ['tag_id'])
    
    # Create collection table
    op.create_table(
        'collection',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_collection_name', 'collection', ['name'], unique=True)
    
    # Create mediaitemcollection association table
    op.create_table(
        'mediaitemcollection',
        sa.Column('media_item_id', sa.Integer(), nullable=True),
        sa.Column('collection_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['media_item_id'], ['mediaitem.id'], ),
        sa.ForeignKeyConstraint(['collection_id'], ['collection.id'], ),
        sa.PrimaryKeyConstraint('media_item_id', 'collection_id')
    )
    op.create_index('ix_mediaitemcollection_media_item_id', 'mediaitemcollection', ['media_item_id'])
    op.create_index('ix_mediaitemcollection_collection_id', 'mediaitemcollection', ['collection_id'])
    
    # Create favorite table
    op.create_table(
        'favorite',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('media_item_id', sa.Integer(), nullable=False),
        sa.Column('favorited_at', sa.DateTime(), nullable=False),
        sa.Column('notes', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['media_item_id'], ['mediaitem.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('media_item_id', name='uq_favorite_media_item_id')
    )
    op.create_index('ix_favorite_media_item_id', 'favorite', ['media_item_id'], unique=True)


def downgrade() -> None:
    """Remove tags, favorites, and collections tables."""
    
    # Drop favorite table
    op.drop_index('ix_favorite_media_item_id', 'favorite')
    op.drop_table('favorite')
    
    # Drop mediaitemcollection association table
    op.drop_index('ix_mediaitemcollection_collection_id', 'mediaitemcollection')
    op.drop_index('ix_mediaitemcollection_media_item_id', 'mediaitemcollection')
    op.drop_table('mediaitemcollection')
    
    # Drop collection table
    op.drop_index('ix_collection_name', 'collection')
    op.drop_table('collection')
    
    # Drop mediaitemtag association table
    op.drop_index('ix_mediaitemtag_tag_id', 'mediaitemtag')
    op.drop_index('ix_mediaitemtag_media_item_id', 'mediaitemtag')
    op.drop_table('mediaitemtag')
    
    # Drop tag table
    op.drop_index('ix_tag_name', 'tag')
    op.drop_table('tag')
