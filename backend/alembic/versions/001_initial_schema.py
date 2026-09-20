"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-09-20 18:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.Float(), nullable=False),
        sa.CheckConstraint("role IN ('ENGINEER', 'MANAGER', 'ADMIN')", name='check_valid_user_role'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('event_id', sa.String(length=64), nullable=False),
        sa.Column('task_id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.String(length=64), nullable=False),
        sa.Column('timestamp', sa.Float(), nullable=False),
        sa.Column('action', sa.String(length=64), nullable=False),
        sa.Column('component', sa.String(length=64), nullable=False),
        sa.Column('details', sa.JSON(), nullable=False),
        sa.Column('checksum', sa.String(length=128), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_audit_events_event_id'), 'audit_events', ['event_id'], unique=False)
    op.create_index(op.f('ix_audit_events_task_id'), 'audit_events', ['task_id'], unique=False)
    op.create_index(op.f('ix_audit_events_user_id'), 'audit_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_events_action'), 'audit_events', ['action'], unique=False)

    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('file_type', sa.String(length=32), nullable=False),
        sa.Column('uploaded_by', sa.String(length=64), nullable=False),
        sa.Column('department', sa.String(length=64), nullable=False),
        sa.Column('classification', sa.String(length=64), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.Float(), nullable=False),
        sa.Column('updated_at', sa.Float(), nullable=False),
        sa.CheckConstraint("status IN ('PENDING', 'INDEXED', 'FAILED')", name='check_valid_document_status'),
        sa.ForeignKeyConstraint(['uploaded_by'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documents_filename'), 'documents', ['filename'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_documents_filename'), table_name='documents')
    op.drop_table('documents')

    op.drop_index(op.f('ix_audit_events_action'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_user_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_task_id'), table_name='audit_events')
    op.drop_index(op.f('ix_audit_events_event_id'), table_name='audit_events')
    op.drop_table('audit_events')

    op.drop_index(op.f('ix_users_username'), table_name='users')
    op.drop_table('users')
