"""ugc_intelligence

Revision ID: 0002_ugc_intelligence
Revises: 0001_initial_schema
Create Date: 2026-10-02 23:55:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002_ugc_intelligence'
down_revision: Union[str, None] = '0001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'asset_intelligence',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('asset_id', sa.Integer(), nullable=False),
        sa.Column('quality_score', sa.Integer(), server_default='0', nullable=False),
        sa.Column('quality_rating', sa.String(length=50), server_default='Needs Review', nullable=False),
        sa.Column('quality_factors', sa.JSON(), nullable=False),
        sa.Column('unavailable_signals', sa.JSON(), nullable=False),
        sa.Column('usage_recommendations', sa.JSON(), nullable=False),
        sa.Column('best_use', sa.String(length=100), nullable=True),
        sa.Column('recommended_format', sa.String(length=50), nullable=True),
        sa.Column('review_decision', sa.String(length=50), server_default='HUMAN_REVIEW', nullable=False),
        sa.Column('review_risk', sa.String(length=20), server_default='MEDIUM', nullable=False),
        sa.Column('review_reason', sa.String(length=500), nullable=True),
        sa.Column('review_confidence', sa.Float(), server_default='0.0', nullable=False),
        sa.Column('explanations', sa.JSON(), nullable=False),
        sa.Column('pipeline_timeline', sa.JSON(), nullable=False),
        sa.Column('version', sa.String(length=20), server_default='1.0.0', nullable=False),
        sa.Column('status', sa.String(length=50), server_default='COMPLETED', nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['asset_id'], ['assets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('asset_id'),
    )
    op.create_index(op.f('ix_asset_intelligence_id'), 'asset_intelligence', ['id'], unique=False)
    op.create_index(op.f('ix_asset_intelligence_asset_id'), 'asset_intelligence', ['asset_id'], unique=True)
    op.create_index('ix_asset_intel_quality_score', 'asset_intelligence', ['quality_score'], unique=False)
    op.create_index('ix_asset_intel_review_decision', 'asset_intelligence', ['review_decision'], unique=False)
    op.create_index('ix_asset_intel_review_risk', 'asset_intelligence', ['review_risk'], unique=False)


def downgrade() -> None:
    op.drop_table('asset_intelligence')
