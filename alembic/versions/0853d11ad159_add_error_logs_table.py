"""add error_logs table

Revision ID: 0853d11ad159
Revises: 2404c05c4f28
Create Date: 2026-07-08 21:03:58.496265

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0853d11ad159'
down_revision: Union[str, Sequence[str], None] = '2404c05c4f28'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('error_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('endpoint', sa.String(), nullable=True),
    sa.Column('method', sa.String(), nullable=True),
    sa.Column('status_code', sa.Integer(), nullable=True),
    sa.Column('error_type', sa.String(), nullable=True),
    sa.Column('error_message', sa.String(), nullable=True),
    sa.Column('traceback', sa.String(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_error_logs_id'), 'error_logs', ['id'], unique=False)
    op.create_index(op.f('ix_error_logs_user_id'), 'error_logs', ['user_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_error_logs_user_id'), table_name='error_logs')
    op.drop_index(op.f('ix_error_logs_id'), table_name='error_logs')
    op.drop_table('error_logs')