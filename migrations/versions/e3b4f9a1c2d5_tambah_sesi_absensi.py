"""tambah sesi_absensi

Revision ID: e3b4f9a1c2d5
Revises: d222f48db0b8
Create Date: 2026-11-10 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'e3b4f9a1c2d5'
down_revision = 'd222f48db0b8'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'sesi_absensi',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('sesi_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('hadir', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('catatan', sa.String(length=255), nullable=True),
        sa.Column('dicatat_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['sesi_id'], ['sesi.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('sesi_id', 'user_id', name='uq_sesi_user'),
    )

def downgrade():
    op.drop_table('sesi_absensi')
