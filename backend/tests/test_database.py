from sqlalchemy import select

from app.database import SessionLocal
from app.models import Category


def test_default_categories_are_seeded() -> None:
    with SessionLocal() as session:
        slugs = set(session.scalars(select(Category.slug)))

    assert slugs == {"people", "places", "food", "school", "daily-life", "transportation"}