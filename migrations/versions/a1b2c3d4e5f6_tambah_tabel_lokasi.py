"""tambah tabel lokasi dan lokasi_id di events

Revision ID: a1b2c3d4e5f6
Revises: f4a5b6c7d8e9
Create Date: 2026-11-10 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = 'f4a5b6c7d8e9'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'lokasi',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nama', sa.String(length=100), nullable=False),
        sa.Column('alamat', sa.String(length=255), nullable=True),
        sa.Column('kapasitas', sa.Integer(), nullable=True),
        sa.Column('keterangan', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nama'),
    )
    op.add_column('events', sa.Column('lokasi_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_events_lokasi_id',
        'events', 'lokasi',
        ['lokasi_id'], ['id'],
        ondelete='SET NULL'
    )


def downgrade():
    op.drop_constraint('fk_events_lokasi_id', 'events', type_='foreignkey')
    op.drop_column('events', 'lokasi_id')
    op.drop_table('lokasi')
