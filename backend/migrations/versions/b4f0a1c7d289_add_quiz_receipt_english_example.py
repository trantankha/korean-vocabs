"""Store English example translations in quiz receipts.

Revision ID: b4f0a1c7d289
Revises: a14c2f9e7b31
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b4f0a1c7d289"
down_revision: Union[str, None] = "a14c2f9e7b31"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("quiz_answer_receipts", sa.Column("example_en", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("quiz_answer_receipts", "example_en")