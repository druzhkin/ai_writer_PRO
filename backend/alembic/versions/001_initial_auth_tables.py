"""Initial authentication tables

Revision ID: 001_initial_auth_tables
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_initial_auth_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial authentication tables."""
    
    # Enable UUID extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('oauth_provider', sa.String(length=50), nullable=True),
        sa.Column('oauth_id', sa.String(length=255), nullable=True),
        sa.Column('avatar_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('email_verification_token', sa.String(length=255), nullable=True),
        sa.Column('email_verification_expires', sa.DateTime(timezone=True), nullable=True),
        sa.Column('password_reset_token', sa.String(length=255), nullable=True),
        sa.Column('password_reset_expires', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for users table
    op.create_index('idx_user_email', 'users', ['email'])
    op.create_index('idx_user_username', 'users', ['username'])
    op.create_index('idx_user_oauth', 'users', ['oauth_provider', 'oauth_id'])
    op.create_index('idx_user_created_at', 'users', ['created_at'])
    
    # Create unique constraints for users table
    op.create_unique_constraint('uq_user_email', 'users', ['email'])
    op.create_unique_constraint('uq_user_username', 'users', ['username'])
    
    # Create organizations table
    op.create_table('organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subscription_plan', sa.String(length=50), nullable=False, server_default=sa.text("'free'")),
        sa.Column('subscription_status', sa.String(length=50), nullable=False, server_default=sa.text("'active'")),
        sa.Column('subscription_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE')
    )
    
    # Create indexes for organizations table
    op.create_index('idx_org_name', 'organizations', ['name'])
    op.create_index('idx_org_slug', 'organizations', ['slug'])
    op.create_index('idx_org_owner', 'organizations', ['owner_id'])
    op.create_index('idx_org_created_at', 'organizations', ['created_at'])
    
    # Create unique constraint for organizations table
    op.create_unique_constraint('uq_org_slug', 'organizations', ['slug'])
    
    # Create organization_members table
    op.create_table('organization_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default=sa.text("'viewer'")),
        sa.Column('invited_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('invitation_token', sa.String(length=255), nullable=True),
        sa.Column('invitation_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('invitation_accepted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_active', sa.String(length=20), nullable=False, server_default=sa.text("'active'")),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by_id'], ['users.id'], ondelete='SET NULL')
    )
    
    # Create indexes for organization_members table
    op.create_index('idx_org_member_user', 'organization_members', ['user_id'])
    op.create_index('idx_org_member_org', 'organization_members', ['organization_id'])
    op.create_index('idx_org_member_role', 'organization_members', ['role'])
    op.create_index('idx_org_member_status', 'organization_members', ['is_active'])
    
    # Create unique constraint for organization_members table
    op.create_unique_constraint('uq_user_organization', 'organization_members', ['user_id', 'organization_id'])
    
    # Create trigger to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Create triggers for updated_at
    op.execute("""
        CREATE TRIGGER update_users_updated_at 
        BEFORE UPDATE ON users 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_organizations_updated_at 
        BEFORE UPDATE ON organizations 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_organization_members_updated_at 
        BEFORE UPDATE ON organization_members 
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Drop initial authentication tables."""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS update_organization_members_updated_at ON organization_members;")
    op.execute("DROP TRIGGER IF EXISTS update_organizations_updated_at ON organizations;")
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users;")
    
    # Drop function
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop tables
    op.drop_table('organization_members')
    op.drop_table('organizations')
    op.drop_table('users')
    
    # Drop UUID extension (optional - might be used by other tables)
    # op.execute('DROP EXTENSION IF EXISTS "uuid-ossp"')
