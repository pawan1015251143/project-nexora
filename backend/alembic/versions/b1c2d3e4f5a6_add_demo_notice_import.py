"""Add demo notice import system

Revision ID: b1c2d3e4f5a6
Revises: 37276a0e1820
Create Date: 2026-09-13 11:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, Sequence[str], None] = '37276a0e1820'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add demo_source_messages and notice_imports tables."""

    # demo_source_messages
    op.create_table(
        'demo_source_messages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_message_id', sa.String(), nullable=False),
        sa.Column('group_name', sa.String(), nullable=False),
        sa.Column('sender', sa.String(), nullable=False),
        sa.Column('message_text', sa.Text(), nullable=False),
        sa.Column('attachment_name', sa.String(), nullable=True),
        sa.Column('attachment_type', sa.String(), nullable=True),
        sa.Column('attachment_content', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.Column('imported', sa.Boolean(), nullable=False, default=False),
        sa.Column('content_hash', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_demo_source_messages_id'), 'demo_source_messages', ['id'], unique=False)
    op.create_index(op.f('ix_demo_source_messages_source_message_id'), 'demo_source_messages', ['source_message_id'], unique=True)
    op.create_index(op.f('ix_demo_source_messages_content_hash'), 'demo_source_messages', ['content_hash'], unique=False)

    # notice_imports status enum
    import_status_enum = sa.Enum(
        'new', 'imported', 'processing', 'draft', 'pending_approval',
        'approved', 'rejected', 'published',
        name='importstatusenum'
    )

    # notice_imports
    op.create_table(
        'notice_imports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('source_message_id', sa.Integer(), nullable=False),
        sa.Column('notice_id', sa.Integer(), nullable=True),
        sa.Column('document_id', sa.Integer(), nullable=True),
        sa.Column('status', import_status_enum, nullable=True),
        sa.Column('ai_extracted_json', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('draft_title', sa.String(), nullable=True),
        sa.Column('draft_content', sa.Text(), nullable=True),
        sa.Column('draft_notice_type', sa.String(), nullable=True),
        sa.Column('processing_error', sa.Text(), nullable=True),
        sa.Column('imported_at', sa.DateTime(), nullable=True),
        sa.Column('processed_at', sa.DateTime(), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('rejected_at', sa.DateTime(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['source_message_id'], ['demo_source_messages.id'], ),
        sa.ForeignKeyConstraint(['notice_id'], ['notices.id'], ),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notice_imports_id'), 'notice_imports', ['id'], unique=False)
    op.create_index(op.f('ix_notice_imports_source_message_id'), 'notice_imports', ['source_message_id'], unique=False)
    op.create_index(op.f('ix_notice_imports_status'), 'notice_imports', ['status'], unique=False)


def downgrade() -> None:
    """Remove demo notice import tables."""
    op.drop_index(op.f('ix_notice_imports_status'), table_name='notice_imports')
    op.drop_index(op.f('ix_notice_imports_source_message_id'), table_name='notice_imports')
    op.drop_index(op.f('ix_notice_imports_id'), table_name='notice_imports')
    op.drop_table('notice_imports')

    op.drop_index(op.f('ix_demo_source_messages_content_hash'), table_name='demo_source_messages')
    op.drop_index(op.f('ix_demo_source_messages_source_message_id'), table_name='demo_source_messages')
    op.drop_index(op.f('ix_demo_source_messages_id'), table_name='demo_source_messages')
    op.drop_table('demo_source_messages')

    sa.Enum(name='importstatusenum').drop(op.get_bind(), checkfirst=False)
