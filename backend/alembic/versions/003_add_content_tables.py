"""add content generation tables

Revision ID: 003_add_content_tables
Revises: 002_add_style_tables
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_content_tables'
down_revision = '002_add_style_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create generated_content table
    op.create_table('generated_content',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('style_profile_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('brief', sa.Text(), nullable=True),
        sa.Column('content_type', sa.String(length=50), nullable=False),
        sa.Column('generated_text', sa.Text(), nullable=False),
        sa.Column('word_count', sa.Integer(), nullable=False),
        sa.Column('character_count', sa.Integer(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('is_current', sa.Boolean(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('estimated_cost', sa.Float(), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=False),
        sa.Column('generation_time_seconds', sa.Float(), nullable=True),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('is_archived', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['style_profile_id'], ['style_profiles.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for generated_content
    op.create_index('idx_generated_content_org', 'generated_content', ['organization_id'], unique=False)
    op.create_index('idx_generated_content_creator', 'generated_content', ['created_by_id'], unique=False)
    op.create_index('idx_generated_content_style', 'generated_content', ['style_profile_id'], unique=False)
    op.create_index('idx_generated_content_created_at', 'generated_content', ['created_at'], unique=False)
    op.create_index('idx_generated_content_status', 'generated_content', ['status'], unique=False)
    op.create_index('idx_generated_content_type', 'generated_content', ['content_type'], unique=False)
    op.create_index('idx_generated_content_current', 'generated_content', ['is_current'], unique=False)
    
    # Create check constraints for generated_content
    op.create_check_constraint('ck_generated_content_word_count_positive', 'generated_content', 'word_count >= 0')
    op.create_check_constraint('ck_generated_content_char_count_positive', 'generated_content', 'character_count >= 0')
    op.create_check_constraint('ck_generated_content_input_tokens_positive', 'generated_content', 'input_tokens >= 0')
    op.create_check_constraint('ck_generated_content_output_tokens_positive', 'generated_content', 'output_tokens >= 0')
    op.create_check_constraint('ck_generated_content_total_tokens_positive', 'generated_content', 'total_tokens >= 0')
    op.create_check_constraint('ck_generated_content_cost_positive', 'generated_content', 'estimated_cost >= 0')
    op.create_check_constraint('ck_generated_content_version_positive', 'generated_content', 'version > 0')

    # Create content_iterations table
    op.create_table('content_iterations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('generated_content_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('edited_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('iteration_number', sa.Integer(), nullable=False),
        sa.Column('edit_prompt', sa.Text(), nullable=False),
        sa.Column('edit_type', sa.String(length=50), nullable=False),
        sa.Column('previous_text', sa.Text(), nullable=False),
        sa.Column('new_text', sa.Text(), nullable=False),
        sa.Column('diff_summary', sa.Text(), nullable=True),
        sa.Column('previous_word_count', sa.Integer(), nullable=False),
        sa.Column('new_word_count', sa.Integer(), nullable=False),
        sa.Column('word_count_change', sa.Integer(), nullable=False),
        sa.Column('previous_character_count', sa.Integer(), nullable=False),
        sa.Column('new_character_count', sa.Integer(), nullable=False),
        sa.Column('character_count_change', sa.Integer(), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('estimated_cost', sa.Float(), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=False),
        sa.Column('generation_time_seconds', sa.Float(), nullable=True),
        sa.Column('generation_prompt', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['edited_by_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['generated_content_id'], ['generated_content.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for content_iterations
    op.create_index('idx_content_iteration_content', 'content_iterations', ['generated_content_id'], unique=False)
    op.create_index('idx_content_iteration_editor', 'content_iterations', ['edited_by_id'], unique=False)
    op.create_index('idx_content_iteration_number', 'content_iterations', ['iteration_number'], unique=False)
    op.create_index('idx_content_iteration_created_at', 'content_iterations', ['created_at'], unique=False)
    op.create_index('idx_content_iteration_type', 'content_iterations', ['edit_type'], unique=False)
    op.create_index('idx_content_iteration_status', 'content_iterations', ['status'], unique=False)
    
    # Create check constraints for content_iterations
    op.create_check_constraint('ck_content_iteration_number_positive', 'content_iterations', 'iteration_number > 0')
    op.create_check_constraint('ck_content_iteration_prev_word_count_positive', 'content_iterations', 'previous_word_count >= 0')
    op.create_check_constraint('ck_content_iteration_new_word_count_positive', 'content_iterations', 'new_word_count >= 0')
    op.create_check_constraint('ck_content_iteration_prev_char_count_positive', 'content_iterations', 'previous_character_count >= 0')
    op.create_check_constraint('ck_content_iteration_new_char_count_positive', 'content_iterations', 'new_character_count >= 0')
    op.create_check_constraint('ck_content_iteration_input_tokens_positive', 'content_iterations', 'input_tokens >= 0')
    op.create_check_constraint('ck_content_iteration_output_tokens_positive', 'content_iterations', 'output_tokens >= 0')
    op.create_check_constraint('ck_content_iteration_total_tokens_positive', 'content_iterations', 'total_tokens >= 0')
    op.create_check_constraint('ck_content_iteration_cost_positive', 'content_iterations', 'estimated_cost >= 0')

    # Create api_usage table
    op.create_table('api_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('service_type', sa.String(length=50), nullable=False),
        sa.Column('operation_type', sa.String(length=50), nullable=False),
        sa.Column('input_tokens', sa.Integer(), nullable=False),
        sa.Column('output_tokens', sa.Integer(), nullable=False),
        sa.Column('total_tokens', sa.Integer(), nullable=False),
        sa.Column('input_cost', sa.Float(), nullable=False),
        sa.Column('output_cost', sa.Float(), nullable=False),
        sa.Column('total_cost', sa.Float(), nullable=False),
        sa.Column('model_used', sa.String(length=100), nullable=False),
        sa.Column('input_cost_per_1k', sa.Float(), nullable=False),
        sa.Column('output_cost_per_1k', sa.Float(), nullable=False),
        sa.Column('request_id', sa.String(length=255), nullable=True),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('success', sa.String(length=10), nullable=False),
        sa.Column('usage_date', sa.Date(), nullable=False),
        sa.Column('usage_hour', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for api_usage
    op.create_index('idx_api_usage_org', 'api_usage', ['organization_id'], unique=False)
    op.create_index('idx_api_usage_user', 'api_usage', ['user_id'], unique=False)
    op.create_index('idx_api_usage_date', 'api_usage', ['usage_date'], unique=False)
    op.create_index('idx_api_usage_service', 'api_usage', ['service_type'], unique=False)
    op.create_index('idx_api_usage_operation', 'api_usage', ['operation_type'], unique=False)
    op.create_index('idx_api_usage_model', 'api_usage', ['model_used'], unique=False)
    op.create_index('idx_api_usage_created_at', 'api_usage', ['created_at'], unique=False)
    op.create_index('idx_api_usage_hour', 'api_usage', ['usage_hour'], unique=False)
    op.create_index('idx_api_usage_success', 'api_usage', ['success'], unique=False)
    
    # Create check constraints for api_usage
    op.create_check_constraint('ck_api_usage_input_tokens_positive', 'api_usage', 'input_tokens >= 0')
    op.create_check_constraint('ck_api_usage_output_tokens_positive', 'api_usage', 'output_tokens >= 0')
    op.create_check_constraint('ck_api_usage_total_tokens_positive', 'api_usage', 'total_tokens >= 0')
    op.create_check_constraint('ck_api_usage_input_cost_positive', 'api_usage', 'input_cost >= 0')
    op.create_check_constraint('ck_api_usage_output_cost_positive', 'api_usage', 'output_cost >= 0')
    op.create_check_constraint('ck_api_usage_total_cost_positive', 'api_usage', 'total_cost >= 0')
    op.create_check_constraint('ck_api_usage_input_cost_per_1k_positive', 'api_usage', 'input_cost_per_1k >= 0')
    op.create_check_constraint('ck_api_usage_output_cost_per_1k_positive', 'api_usage', 'output_cost_per_1k >= 0')
    op.create_check_constraint('ck_api_usage_hour_valid', 'api_usage', 'usage_hour >= 0 AND usage_hour <= 23')
    op.create_check_constraint('ck_api_usage_response_time_positive', 'api_usage', 'response_time_ms >= 0')


def downgrade() -> None:
    # Drop api_usage table
    op.drop_check_constraint('ck_api_usage_response_time_positive', 'api_usage')
    op.drop_check_constraint('ck_api_usage_hour_valid', 'api_usage')
    op.drop_check_constraint('ck_api_usage_output_cost_per_1k_positive', 'api_usage')
    op.drop_check_constraint('ck_api_usage_input_cost_per_1k_positive', 'api_usage')
    op.drop_check_constraint('ck_api_usage_total_cost_positive', 'api_usage')
    op.drop_check_constraint('ck_api_usage_output_cost_positive', 'api_usage')
    op.drop_check_constraint('ck_api_usage_input_cost_positive', 'api_usage')
    op.drop_check_constraint('ck_api_usage_total_tokens_positive', 'api_usage')
    op.drop_check_constraint('ck_api_usage_output_tokens_positive', 'api_usage')
    op.drop_check_constraint('ck_api_usage_input_tokens_positive', 'api_usage')
    
    op.drop_index('idx_api_usage_success', table_name='api_usage')
    op.drop_index('idx_api_usage_hour', table_name='api_usage')
    op.drop_index('idx_api_usage_created_at', table_name='api_usage')
    op.drop_index('idx_api_usage_model', table_name='api_usage')
    op.drop_index('idx_api_usage_operation', table_name='api_usage')
    op.drop_index('idx_api_usage_service', table_name='api_usage')
    op.drop_index('idx_api_usage_date', table_name='api_usage')
    op.drop_index('idx_api_usage_user', table_name='api_usage')
    op.drop_index('idx_api_usage_org', table_name='api_usage')
    op.drop_table('api_usage')

    # Drop content_iterations table
    op.drop_check_constraint('ck_content_iteration_cost_positive', 'content_iterations')
    op.drop_check_constraint('ck_content_iteration_total_tokens_positive', 'content_iterations')
    op.drop_check_constraint('ck_content_iteration_output_tokens_positive', 'content_iterations')
    op.drop_check_constraint('ck_content_iteration_input_tokens_positive', 'content_iterations')
    op.drop_check_constraint('ck_content_iteration_new_char_count_positive', 'content_iterations')
    op.drop_check_constraint('ck_content_iteration_prev_char_count_positive', 'content_iterations')
    op.drop_check_constraint('ck_content_iteration_new_word_count_positive', 'content_iterations')
    op.drop_check_constraint('ck_content_iteration_prev_word_count_positive', 'content_iterations')
    op.drop_check_constraint('ck_content_iteration_number_positive', 'content_iterations')
    
    op.drop_index('idx_content_iteration_status', table_name='content_iterations')
    op.drop_index('idx_content_iteration_type', table_name='content_iterations')
    op.drop_index('idx_content_iteration_created_at', table_name='content_iterations')
    op.drop_index('idx_content_iteration_number', table_name='content_iterations')
    op.drop_index('idx_content_iteration_editor', table_name='content_iterations')
    op.drop_index('idx_content_iteration_content', table_name='content_iterations')
    op.drop_table('content_iterations')

    # Drop generated_content table
    op.drop_check_constraint('ck_generated_content_version_positive', 'generated_content')
    op.drop_check_constraint('ck_generated_content_cost_positive', 'generated_content')
    op.drop_check_constraint('ck_generated_content_total_tokens_positive', 'generated_content')
    op.drop_check_constraint('ck_generated_content_output_tokens_positive', 'generated_content')
    op.drop_check_constraint('ck_generated_content_input_tokens_positive', 'generated_content')
    op.drop_check_constraint('ck_generated_content_char_count_positive', 'generated_content')
    op.drop_check_constraint('ck_generated_content_word_count_positive', 'generated_content')
    
    op.drop_index('idx_generated_content_current', table_name='generated_content')
    op.drop_index('idx_generated_content_type', table_name='generated_content')
    op.drop_index('idx_generated_content_status', table_name='generated_content')
    op.drop_index('idx_generated_content_created_at', table_name='generated_content')
    op.drop_index('idx_generated_content_style', table_name='generated_content')
    op.drop_index('idx_generated_content_creator', table_name='generated_content')
    op.drop_index('idx_generated_content_org', table_name='generated_content')
    op.drop_table('generated_content')
