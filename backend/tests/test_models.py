from app.database import Base
from app.models import Category, User, Vocabulary


def test_initial_models_register_expected_tables() -> None:
    assert set(Base.metadata.tables) == {
        "users",
        "categories",
        "vocabularies",
        "vocabulary_progress",
        "quiz_answer_receipts",
    }


def test_vocabulary_requires_category_and_level_but_allows_shared_owner() -> None:
    table = Vocabulary.__table__

    assert table.c.user_id.nullable
    assert not table.c.category_id.nullable
    assert not table.c.level.nullable
    assert table.c.example_en.nullable
    assert any(constraint.name == "ck_vocabularies_level" for constraint in table.constraints)
    assert User.__tablename__ == "users"
    assert Category.__tablename__ == "categories"