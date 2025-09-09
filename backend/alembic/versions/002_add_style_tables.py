"""add style tables

Revision ID: 002_add_style_tables
Revises: 001_initial_auth_tables
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_style_tables'
down_revision = '001_initial_auth_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create style_profiles table
    op.create_table('style_profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('analysis', sa.JSON(), nullable=False),
        sa.Column('tags', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('last_analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('organization_id', 'name', name='uq_style_profile_org_name')
    )
    op.create_index('idx_style_profile_org', 'style_profiles', ['organization_id'], unique=False)
    op.create_index('idx_style_profile_created_by', 'style_profiles', ['created_by_id'], unique=False)
    op.create_index('idx_style_profile_created_at', 'style_profiles', ['created_at'], unique=False)
    op.create_index('idx_style_profile_last_analyzed', 'style_profiles', ['last_analyzed_at'], unique=False)

    # Create reference_articles table
    op.create_table('reference_articles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('source_url', sa.Text(), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=True),
        sa.Column('file_size', sa.String(length=50), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('s3_key', sa.String(length=500), nullable=True),
        sa.Column('style_profile_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('processing_status', sa.String(length=50), nullable=False),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['style_profile_id'], ['style_profiles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_reference_article_style_profile', 'reference_articles', ['style_profile_id'], unique=False)
    op.create_index('idx_reference_article_uploaded_by', 'reference_articles', ['uploaded_by_id'], unique=False)
    op.create_index('idx_reference_article_organization', 'reference_articles', ['organization_id'], unique=False)
    op.create_index('idx_reference_article_created_at', 'reference_articles', ['created_at'], unique=False)
    op.create_index('idx_reference_article_processing_status', 'reference_articles', ['processing_status'], unique=False)
    op.create_index('idx_reference_article_processed_at', 'reference_articles', ['processed_at'], unique=False)


def downgrade() -> None:
    # Drop reference_articles table
    op.drop_index('idx_reference_article_processed_at', table_name='reference_articles')
    op.drop_index('idx_reference_article_processing_status', table_name='reference_articles')
    op.drop_index('idx_reference_article_created_at', table_name='reference_articles')
    op.drop_index('idx_reference_article_organization', table_name='reference_articles')
    op.drop_index('idx_reference_article_uploaded_by', table_name='reference_articles')
    op.drop_index('idx_reference_article_style_profile', table_name='reference_articles')
    op.drop_table('reference_articles')

    # Drop style_profiles table
    op.drop_index('idx_style_profile_last_analyzed', table_name='style_profiles')
    op.drop_index('idx_style_profile_created_at', table_name='style_profiles')
    op.drop_index('idx_style_profile_created_by', table_name='style_profiles')
    op.drop_index('idx_style_profile_org', table_name='style_profiles')
    op.drop_table('style_profiles')
