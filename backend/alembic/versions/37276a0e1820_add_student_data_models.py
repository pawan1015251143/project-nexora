"""Add student data models

Revision ID: 37276a0e1820
Revises: 97aef22ba29d
Create Date: 2026-09-13 10:55:06.285567

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '37276a0e1820'
down_revision: Union[str, Sequence[str], None] = '97aef22ba29d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'student_attendance',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subject_name', sa.String(), nullable=False),
        sa.Column('total_classes', sa.Integer(), nullable=False),
        sa.Column('attended_classes', sa.Integer(), nullable=False),
        sa.Column('percentage', sa.Float(), nullable=False),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_attendance_id'), 'student_attendance', ['id'], unique=False)

    op.create_table(
        'student_subject_marks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('subject_name', sa.String(), nullable=False),
        sa.Column('marks_obtained', sa.Float(), nullable=False),
        sa.Column('total_marks', sa.Float(), nullable=False),
        sa.Column('grade', sa.String(), nullable=True),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_subject_marks_id'), 'student_subject_marks', ['id'], unique=False)

    op.create_table(
        'student_fee_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_fee', sa.Float(), nullable=False),
        sa.Column('paid_fee', sa.Float(), nullable=False),
        sa.Column('pending_fee', sa.Float(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('semester', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_student_fee_records_id'), 'student_fee_records', ['id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_student_fee_records_id'), table_name='student_fee_records')
    op.drop_table('student_fee_records')
    op.drop_index(op.f('ix_student_subject_marks_id'), table_name='student_subject_marks')
    op.drop_table('student_subject_marks')
    op.drop_index(op.f('ix_student_attendance_id'), table_name='student_attendance')
    op.drop_table('student_attendance')
