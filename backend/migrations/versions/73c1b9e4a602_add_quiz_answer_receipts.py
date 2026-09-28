"""Add idempotent quiz answer receipts.

Revision ID: 73c1b9e4a602
Revises: 2f4d8a1c7e30
Create Date: 2026-09-28
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "73c1b9e4a602"
down_revision: Union[str, None] = "2f4d8a1c7e30"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "quiz_answer_receipts",
        sa.Column("token_id", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("vocabulary_id", sa.Integer(), nullable=False),
        sa.Column("selected_choice_id", sa.String(length=32), nullable=False),
        sa.Column("correct", sa.Boolean(), nullable=False),
        sa.Column("selected_answer", sa.Text(), nullable=False),
        sa.Column("correct_answer", sa.Text(), nullable=False),
        sa.Column("example", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["vocabulary_id"], ["vocabularies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("token_id"),
    )
    op.create_index(
        "ix_quiz_answer_receipts_created_at",
        "quiz_answer_receipts",
        ["created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_quiz_answer_receipts_created_at", table_name="quiz_answer_receipts")
    op.drop_table("quiz_answer_receipts")