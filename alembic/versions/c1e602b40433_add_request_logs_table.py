"""add request_logs table

Revision ID: c1e602b40433
Revises: 0853d11ad159
Create Date: 2026-07-08 22:01:19.597195

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1e602b40433'
down_revision: Union[str, Sequence[str], None] = '0853d11ad159'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('request_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('endpoint', sa.String(), nullable=True),
    sa.Column('method', sa.String(), nullable=True),
    sa.Column('status_code', sa.Integer(), nullable=True),
    sa.Column('duration_ms', sa.Float(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_request_logs_id'), 'request_logs', ['id'], unique=False)
    op.create_index(op.f('ix_request_logs_user_id'), 'request_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_request_logs_endpoint'), 'request_logs', ['endpoint'], unique=False)
    op.create_index(op.f('ix_request_logs_created_at'), 'request_logs', ['created_at'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_request_logs_created_at'), table_name='request_logs')
    op.drop_index(op.f('ix_request_logs_endpoint'), table_name='request_logs')
    op.drop_index(op.f('ix_request_logs_user_id'), table_name='request_logs')
    op.drop_index(op.f('ix_request_logs_id'), table_name='request_logs')
    op.drop_table('request_logs')