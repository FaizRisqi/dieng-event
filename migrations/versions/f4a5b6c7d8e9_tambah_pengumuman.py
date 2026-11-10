"""tambah pengumuman

Revision ID: f4a5b6c7d8e9
Revises: e3b4f9a1c2d5
Create Date: 2026-11-10 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'f4a5b6c7d8e9'
down_revision = 'e3b4f9a1c2d5'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'pengumuman',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('judul', sa.String(length=150), nullable=False),
        sa.Column('isi', sa.Text(), nullable=False),
        sa.Column('pin', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('community_id', sa.Integer(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['community_id'], ['communities.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )


def downgrade():
    op.drop_table('pengumuman')
