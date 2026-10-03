"""initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-10-02 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create assets table
    op.create_table(
        'assets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('public_id', sa.String(length=64), nullable=False),
        sa.Column('cloudinary_public_id', sa.String(length=255), nullable=False),
        sa.Column('cloudinary_url', sa.String(length=1024), nullable=True),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('mime_type', sa.String(length=64), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('width', sa.Integer(), nullable=True),
        sa.Column('height', sa.Integer(), nullable=True),
        sa.Column(
            'status',
            sa.Enum('PROCESSING', 'PENDING', 'APPROVED', 'REJECTED', 'FAILED', name='asset_status_enum'),
            nullable=False,
            server_default='PENDING',
        ),
        sa.Column(
            'moderation_status',
            sa.Enum('PENDING', 'APPROVED', 'REJECTED', name='moderation_status_enum'),
            nullable=False,
            server_default='PENDING',
        ),
        sa.Column('moderation_reason', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejected_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('decision_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_assets_id'), 'assets', ['id'], unique=False)
    op.create_index(op.f('ix_assets_public_id'), 'assets', ['public_id'], unique=True)
    op.create_index(op.f('ix_assets_cloudinary_public_id'), 'assets', ['cloudinary_public_id'], unique=True)
    op.create_index(op.f('ix_assets_status'), 'assets', ['status'], unique=False)
    op.create_index(op.f('ix_assets_moderation_status'), 'assets', ['moderation_status'], unique=False)
    op.create_index(op.f('ix_assets_created_at'), 'assets', ['created_at'], unique=False)
    op.create_index('ix_assets_status_created_at', 'assets', ['status', 'created_at'], unique=False)
    op.create_index('ix_assets_moderation_status_created_at', 'assets', ['moderation_status', 'created_at'], unique=False)

    # 2. Create asset_tags table
    op.create_table(
        'asset_tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('tag', sa.String(length=100), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id', 'tag', name='uq_asset_tag'),
    )
    op.create_index(op.f('ix_asset_tags_id'), 'asset_tags', ['id'], unique=False)
    op.create_index(op.f('ix_asset_tags_asset_id'), 'asset_tags', ['asset_id'], unique=False)
    op.create_index(op.f('ix_asset_tags_tag'), 'asset_tags', ['tag'], unique=False)
    op.create_index('ix_asset_tags_tag_confidence', 'asset_tags', ['tag', 'confidence'], unique=False)

    # 3. Create processing_states table
    op.create_table(
        'processing_states',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column(
            'tagging_status',
            sa.Enum('NOT_REQUESTED', 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='tagging_status_enum'),
            nullable=False,
            server_default='PENDING',
        ),
        sa.Column(
            'moderation_status',
            sa.Enum('NOT_REQUESTED', 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='proc_moderation_status_enum'),
            nullable=False,
            server_default='PENDING',
        ),
        sa.Column(
            'background_removal_status',
            sa.Enum('NOT_REQUESTED', 'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED', name='bg_removal_status_enum'),
            nullable=False,
            server_default='NOT_REQUESTED',
        ),
        sa.Column('processing_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('processing_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id'),
    )
    op.create_index(op.f('ix_processing_states_id'), 'processing_states', ['id'], unique=False)
    op.create_index(op.f('ix_processing_states_asset_id'), 'processing_states', ['asset_id'], unique=True)


def downgrade() -> None:
    op.drop_table('processing_states')
    op.drop_table('asset_tags')
    op.drop_table('assets')
    op.execute('DROP TYPE IF EXISTS asset_status_enum;')
    op.execute('DROP TYPE IF EXISTS moderation_status_enum;')
    op.execute('DROP TYPE IF EXISTS tagging_status_enum;')
    op.execute('DROP TYPE IF EXISTS proc_moderation_status_enum;')
    op.execute('DROP TYPE IF EXISTS bg_removal_status_enum;')
