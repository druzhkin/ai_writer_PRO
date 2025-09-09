"""add diff_lines to content_iterations

Revision ID: 004_add_diff_lines_to_content_iterations
Revises: 003_add_content_tables
Create Date: 2024-01-01 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004_add_diff_lines_to_content_iterations'
down_revision = '003_add_content_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add diff_lines column to content_iterations table
    op.add_column('content_iterations', sa.Column('diff_lines', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove diff_lines column from content_iterations table
    op.drop_column('content_iterations', 'diff_lines')
