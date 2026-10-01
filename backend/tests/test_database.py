from sqlalchemy import select

from app.database import SessionLocal
from app.models import Category
from app.seed_vocabulary import CATEGORY_NAMES


def test_default_categories_are_seeded() -> None:
    with SessionLocal() as session:
        categories = {
            category.slug: category.name_en
            for category in session.scalars(select(Category)).all()
        }

    assert categories == CATEGORY_NAMES