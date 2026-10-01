from collections import Counter

from sqlalchemy import select

from app.database import SessionLocal
from app.models import Vocabulary
from app.seed_vocabulary import CATEGORY_TARGETS, load_seed_rows, seed_vocabulary


def test_seed_dataset_has_250_complete_beginner_rows_with_target_distribution() -> None:
    rows = load_seed_rows()

    assert len(rows) == 250
    assert Counter(row["category_slug"] for row in rows) == Counter(CATEGORY_TARGETS)
    assert all(row["example_ko"] and row["example_en"] for row in rows)


def test_seed_command_is_idempotent_and_creates_shared_beginner_rows() -> None:
    with SessionLocal() as session:
        first_run = seed_vocabulary(session)
        second_run = seed_vocabulary(session)

        assert first_run.dataset_size == 250
        assert first_run.inserted + first_run.already_present == 250
        assert second_run.inserted == 0
        assert second_run.updated == 0
        assert second_run.already_present == 250

        expected_rows = {row["word"]: row for row in load_seed_rows()}
        records = session.scalars(
            select(Vocabulary).where(
                Vocabulary.user_id.is_(None),
                Vocabulary.word.in_(expected_rows),
            )
        ).all()
        assert len(records) == 250
        for record in records:
            expected = expected_rows[record.word]
            assert record.level == "BEGINNER"
            assert record.meaning == expected["meaning"]
            assert record.example == expected["example_ko"]
            assert record.example_en == expected["example_en"]
            assert record.category.slug == expected["category_slug"]
