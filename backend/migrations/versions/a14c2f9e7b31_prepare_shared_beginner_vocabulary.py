"""Prepare schema and categories for shared beginner vocabulary.

Revision ID: a14c2f9e7b31
Revises: 73c1b9e4a602
Create Date: 2026-09-30
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a14c2f9e7b31"
down_revision: Union[str, None] = "73c1b9e4a602"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "vocabularies",
        "user_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
    op.add_column("vocabularies", sa.Column("example_en", sa.Text(), nullable=True))
    op.execute(
        sa.text(
            "UPDATE categories SET name_en = CASE slug "
            "WHEN 'people' THEN 'People & Family' "
            "WHEN 'food' THEN 'Food & Drinks' "
            "WHEN 'school' THEN 'School & Study' "
            "WHEN 'daily-life' THEN 'Daily Life' "
            "ELSE name_en END"
        )
    )

    categories = sa.table(
        "categories",
        sa.column("slug", sa.String(length=50)),
        sa.column("name_ko", sa.String(length=100)),
        sa.column("name_en", sa.String(length=100)),
    )
    op.bulk_insert(
        categories,
        [
            {"slug": "time-dates", "name_ko": "시간과 날짜", "name_en": "Time & Dates"},
            {"slug": "actions", "name_ko": "행동", "name_en": "Actions"},
            {"slug": "descriptions", "name_ko": "묘사", "name_en": "Descriptions"},
            {"slug": "objects-things", "name_ko": "사물", "name_en": "Objects & Things"},
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM quiz_answer_receipts WHERE vocabulary_id IN "
            "(SELECT id FROM vocabularies WHERE user_id IS NULL)"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM vocabulary_progress WHERE vocabulary_id IN "
            "(SELECT id FROM vocabularies WHERE user_id IS NULL)"
        )
    )
    op.execute(sa.text("DELETE FROM vocabularies WHERE user_id IS NULL"))
    op.execute(
        sa.text(
            "UPDATE categories SET name_en = CASE slug "
            "WHEN 'people' THEN 'People' "
            "WHEN 'food' THEN 'Food' "
            "WHEN 'school' THEN 'School' "
            "WHEN 'daily-life' THEN 'Daily life' "
            "ELSE name_en END"
        )
    )
    op.execute(
        sa.text(
            "DELETE FROM categories WHERE slug IN "
            "('time-dates', 'actions', 'descriptions', 'objects-things') "
            "AND NOT EXISTS (SELECT 1 FROM vocabularies WHERE category_id = categories.id)"
        )
    )
    op.drop_column("vocabularies", "example_en")
    op.alter_column(
        "vocabularies",
        "user_id",
        existing_type=sa.Integer(),
        nullable=False,
    )