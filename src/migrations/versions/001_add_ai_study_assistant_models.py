"""Add AI Study Assistant models (Document, Question, StudySession)

Revision ID: 001_ai_study_assistant
Revises:
Create Date: 2025-06-11 21:54:16.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001_ai_study_assistant'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create document table
    op.create_table('document',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('title', sa.String(length=200), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=False),
    sa.Column('file_type', sa.String(length=10), nullable=False),
    sa.Column('file_size', sa.Integer(), nullable=False),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id', 'uuid'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_document_is_deleted'), 'document', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_document_user_id'), 'document', ['user_id'], unique=False)

    # Create question table
    op.create_table('question',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('question_text', sa.Text(), nullable=False),
    sa.Column('question_type', sa.String(length=50), nullable=False),
    sa.Column('correct_answer', sa.Text(), nullable=False),
    sa.Column('options', sa.Text(), nullable=True),
    sa.Column('explanation', sa.Text(), nullable=True),
    sa.Column('difficulty', sa.String(length=20), nullable=False),
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id', 'uuid'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_question_document_id'), 'question', ['document_id'], unique=False)
    op.create_index(op.f('ix_question_is_deleted'), 'question', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_question_user_id'), 'question', ['user_id'], unique=False)

    # Create study_session table
    op.create_table('study_session',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('session_name', sa.String(length=200), nullable=False),
    sa.Column('total_questions', sa.Integer(), nullable=False),
    sa.Column('correct_answers', sa.Integer(), nullable=False),
    sa.Column('score_percentage', sa.Float(), nullable=True),
    sa.Column('time_spent_minutes', sa.Integer(), nullable=True),
    sa.Column('answers', sa.Text(), nullable=True),
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('document_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['document.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id', 'uuid'),
    sa.UniqueConstraint('id'),
    sa.UniqueConstraint('uuid')
    )
    op.create_index(op.f('ix_study_session_document_id'), 'study_session', ['document_id'], unique=False)
    op.create_index(op.f('ix_study_session_is_deleted'), 'study_session', ['is_deleted'], unique=False)
    op.create_index(op.f('ix_study_session_user_id'), 'study_session', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_study_session_user_id'), table_name='study_session')
    op.drop_index(op.f('ix_study_session_is_deleted'), table_name='study_session')
    op.drop_index(op.f('ix_study_session_document_id'), table_name='study_session')
    op.drop_table('study_session')
    op.drop_index(op.f('ix_question_user_id'), table_name='question')
    op.drop_index(op.f('ix_question_is_deleted'), table_name='question')
    op.drop_index(op.f('ix_question_document_id'), table_name='question')
    op.drop_table('question')
    op.drop_index(op.f('ix_document_user_id'), table_name='document')
    op.drop_index(op.f('ix_document_is_deleted'), table_name='document')
    op.drop_table('document')
