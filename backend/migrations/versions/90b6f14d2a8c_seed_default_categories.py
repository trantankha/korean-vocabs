"""Seed the predefined vocabulary categories.

Revision ID: 90b6f14d2a8c
Revises: fb3766b7322a
Create Date: 2026-09-27
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "90b6f14d2a8c"
down_revision: Union[str, None] = "fb3766b7322a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    categories = sa.table(
        "categories",
        sa.column("slug", sa.String(length=50)),
        sa.column("name_ko", sa.String(length=100)),
        sa.column("name_en", sa.String(length=100)),
    )
    op.bulk_insert(
        categories,
        [
            {"slug": "people", "name_ko": "사람", "name_en": "People"},
            {"slug": "places", "name_ko": "장소", "name_en": "Places"},
            {"slug": "food", "name_ko": "음식", "name_en": "Food"},
            {"slug": "school", "name_ko": "학교", "name_en": "School"},
            {"slug": "daily-life", "name_ko": "일상", "name_en": "Daily life"},
            {"slug": "transportation", "name_ko": "교통", "name_en": "Transportation"},
        ],
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DELETE FROM categories "
            "WHERE slug IN ('people', 'places', 'food', 'school', 'daily-life', 'transportation')"
        )
    )