"""Add NoticeTranslation model

Revision ID: 97aef22ba29d
Revises: abc123def456
Create Date: 2026-09-13 10:08:34.982313

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '97aef22ba29d'
down_revision: Union[str, Sequence[str], None] = 'abc123def456'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('notice_translations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('notice_id', sa.Integer(), nullable=False),
    sa.Column('mode', sa.String(), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['notice_id'], ['notices.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notice_translations_id'), 'notice_translations', ['id'], unique=False)
    op.create_index(op.f('ix_notice_translations_mode'), 'notice_translations', ['mode'], unique=False)
    op.create_index(op.f('ix_notice_translations_notice_id'), 'notice_translations', ['notice_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_notice_translations_notice_id'), table_name='notice_translations')
    op.drop_index(op.f('ix_notice_translations_mode'), table_name='notice_translations')
    op.drop_index(op.f('ix_notice_translations_id'), table_name='notice_translations')
    op.drop_table('notice_translations')
