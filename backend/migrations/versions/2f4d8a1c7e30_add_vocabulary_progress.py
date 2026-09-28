"""Add persistent vocabulary learning progress.

Revision ID: 2f4d8a1c7e30
Revises: 90b6f14d2a8c
Create Date: 2026-09-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "2f4d8a1c7e30"
down_revision: Union[str, None] = "90b6f14d2a8c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "vocabulary_progress",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("vocabulary_id", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("review_count", sa.Integer(), nullable=False),
        sa.Column("remembered_count", sa.Integer(), nullable=False),
        sa.Column("not_remembered_count", sa.Integer(), nullable=False),
        sa.Column("last_reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('NEW', 'LEARNING', 'MASTERED')",
            name="ck_vocabulary_progress_status",
        ),
        sa.CheckConstraint(
            "review_count >= 0 AND remembered_count >= 0 AND not_remembered_count >= 0",
            name="ck_vocabulary_progress_counts_nonnegative",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vocabulary_id"], ["vocabularies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "vocabulary_id", name="uq_vocabulary_progress_user_vocabulary"),
    )
    op.create_index(
        "ix_vocabulary_progress_user_status",
        "vocabulary_progress",
        ["user_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_vocabulary_progress_user_status", table_name="vocabulary_progress")
    op.drop_table("vocabulary_progress")