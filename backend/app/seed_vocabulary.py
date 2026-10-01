import csv
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models import Category, Vocabulary

DATASET_PATH = Path(__file__).resolve().parent.parent / "data" / "beginner_vocabulary.csv"
CATEGORY_TARGETS = {
    "people": 25,
    "daily-life": 25,
    "food": 30,
    "places": 25,
    "school": 25,
    "transportation": 20,
    "time-dates": 25,
    "actions": 35,
    "descriptions": 25,
    "objects-things": 15,
}
CATEGORY_NAMES = {
    "people": "People & Family",
    "daily-life": "Daily Life",
    "food": "Food & Drinks",
    "places": "Places",
    "school": "School & Study",
    "transportation": "Transportation",
    "time-dates": "Time & Dates",
    "actions": "Actions",
    "descriptions": "Descriptions",
    "objects-things": "Objects & Things",
}
REQUIRED_FIELDS = ("word", "meaning", "category_slug", "example_ko", "example_en")


@dataclass(frozen=True)
class SeedSummary:
    inserted: int
    updated: int
    already_present: int
    dataset_size: int


def _normalized_word(word: str) -> str:
    return unicodedata.normalize("NFKC", word).strip().casefold()


def load_seed_rows() -> list[dict[str, str]]:
    with DATASET_PATH.open(encoding="utf-8-sig", newline="") as data_file:
        reader = csv.DictReader(data_file)
        if reader.fieldnames is None or not set(REQUIRED_FIELDS).issubset(reader.fieldnames):
            raise ValueError("The vocabulary dataset is missing required columns")
        rows = list(reader)

    normalized_words: set[str] = set()
    category_counts: Counter[str] = Counter()
    for row_number, row in enumerate(rows, start=2):
        for field in REQUIRED_FIELDS:
            value = row.get(field)
            if value is None or not value or value != value.strip():
                raise ValueError(f"Dataset row {row_number} has an empty or untrimmed {field}")

        category_slug = row["category_slug"]
        if category_slug not in CATEGORY_TARGETS:
            raise ValueError(f"Dataset row {row_number} has an unknown category")
        normalized_word = _normalized_word(row["word"])
        if normalized_word in normalized_words:
            raise ValueError(f"Dataset contains a duplicate Korean word: {row['word']}")
        normalized_words.add(normalized_word)
        category_counts[category_slug] += 1

    if len(rows) != 250:
        raise ValueError(f"Expected 250 vocabulary rows, found {len(rows)}")
    if category_counts != Counter(CATEGORY_TARGETS):
        raise ValueError("Dataset category counts do not match the V0.3.1 targets")
    return rows


def seed_vocabulary(session: Session) -> SeedSummary:
    rows = load_seed_rows()
    categories = {
        category.slug: category
        for category in session.scalars(select(Category)).all()
    }
    missing_categories = set(CATEGORY_TARGETS) - categories.keys()
    if missing_categories:
        raise ValueError(f"Missing canonical categories: {', '.join(sorted(missing_categories))}")
    mislabeled_categories = {
        slug
        for slug, name in CATEGORY_NAMES.items()
        if categories[slug].name_en != name
    }
    if mislabeled_categories:
        raise ValueError(f"Non-canonical category labels: {', '.join(sorted(mislabeled_categories))}")

    existing_records = list(
        session.scalars(
            select(Vocabulary).where(Vocabulary.user_id.is_(None))
        ).all()
    )
    existing_word_counts = Counter(_normalized_word(record.word) for record in existing_records)
    duplicate_existing_words = [
        word for word, count in existing_word_counts.items() if count > 1
    ]
    if duplicate_existing_words:
        raise ValueError(
            "Shared vocabulary already contains normalized duplicates: "
            + ", ".join(sorted(duplicate_existing_words))
        )

    existing_by_word = {
        _normalized_word(record.word): record
        for record in existing_records
    }
    new_records: list[Vocabulary] = []
    updated = 0
    already_present = 0
    for row in rows:
        normalized_word = _normalized_word(row["word"])
        existing = existing_by_word.get(normalized_word)
        category_id = categories[row["category_slug"]].id
        if existing is not None:
            already_present += 1
            canonical_fields = {
                "word": row["word"],
                "meaning": row["meaning"],
                "category_id": category_id,
                "level": "BEGINNER",
                "example": row["example_ko"],
                "example_en": row["example_en"],
            }
            if any(getattr(existing, field) != value for field, value in canonical_fields.items()):
                for field, value in canonical_fields.items():
                    setattr(existing, field, value)
                updated += 1
            continue
        new_records.append(
            Vocabulary(
                user_id=None,
                word=row["word"],
                meaning=row["meaning"],
                example=row["example_ko"],
                example_en=row["example_en"],
                category_id=category_id,
                level="BEGINNER",
            )
        )
        existing_by_word[normalized_word] = new_records[-1]

    session.add_all(new_records)
    session.commit()
    return SeedSummary(
        inserted=len(new_records),
        updated=updated,
        already_present=already_present,
        dataset_size=len(rows),
    )


def main() -> None:
    with SessionLocal() as session:
        summary = seed_vocabulary(session)
    print(
        f"Seeded {summary.dataset_size} beginner vocabulary items "
        f"({summary.inserted} inserted, {summary.updated} updated, "
        f"{summary.already_present} already present)."
    )


if __name__ == "__main__":
    main()