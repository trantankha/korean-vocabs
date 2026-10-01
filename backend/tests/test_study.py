from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.auth import create_access_token
from app.database import SessionLocal
from app.main import app
from app.models import Category, User, Vocabulary, VocabularyProgress

TRUSTED_ORIGIN = "http://127.0.0.1:3000"


@pytest.fixture(autouse=True)
def cleanup_study_test_users():
    yield
    with SessionLocal() as session:
        session.execute(delete(User).where(User.email.like("test-study-%@example.com")))
        session.commit()


def create_client_user(client: TestClient) -> int:
    email = f"test-study-{uuid4().hex}@example.com"
    with SessionLocal() as session:
        user = User(email=email, password_hash="unused-test-hash")
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id
        token = create_access_token(user_id)
    client.cookies.set("korean_vocab_access", token)
    return user_id


def add_vocabulary(user_id: int, word: str, category_id: int, level: str = "BEGINNER") -> int:
    with SessionLocal() as session:
        vocabulary = Vocabulary(
            user_id=user_id,
            word=word,
            meaning=f"Meaning of {word}",
            category_id=category_id,
            level=level,
        )
        session.add(vocabulary)
        session.commit()
        session.refresh(vocabulary)
        return vocabulary.id


def get_category_id(slug: str) -> int:
    with SessionLocal() as session:
        category_id = session.scalar(select(Category.id).where(Category.slug == slug))
    assert category_id is not None
    return category_id


def test_study_cards_are_filtered_and_scoped_to_user() -> None:
    with TestClient(app) as owner, TestClient(app) as other_user:
        owner_id = create_client_user(owner)
        other_id = create_client_user(other_user)
        places_id = get_category_id("places")
        food_id = get_category_id("food")
        owned_id = add_vocabulary(owner_id, "학교-test", places_id, "ADVANCED")
        add_vocabulary(owner_id, "사과-test", food_id, "ADVANCED")
        add_vocabulary(other_id, "집-test", places_id, "ADVANCED")

        response = owner.get(
            "/study/cards?category_id="
            f"{places_id}&level=ADVANCED&limit=5"
        )

        assert response.status_code == 200, response.text
        assert [card["id"] for card in response.json()] == [owned_id]


def test_progress_is_persisted_and_other_users_cannot_record_it() -> None:
    with TestClient(app) as owner, TestClient(app) as other_user:
        owner_id = create_client_user(owner)
        create_client_user(other_user)
        vocabulary_id = add_vocabulary(owner_id, "학교", get_category_id("places"))
        headers = {"Origin": TRUSTED_ORIGIN}

        denied = other_user.post(
            "/study/progress",
            json={"vocabulary_id": vocabulary_id, "result": "REMEMBERED"},
            headers=headers,
        )
        assert denied.status_code == 404

        for _ in range(3):
            response = owner.post(
                "/study/progress",
                json={"vocabulary_id": vocabulary_id, "result": "REMEMBERED"},
                headers=headers,
            )
            assert response.status_code == 200

        result = response.json()
        assert result["status"] == "MASTERED"
        assert result["review_count"] == 3
        assert result["remembered_count"] == 3
        assert result["not_remembered_count"] == 0

        with SessionLocal() as session:
            progress = session.scalar(
                select(VocabularyProgress).where(
                    VocabularyProgress.user_id == owner_id,
                    VocabularyProgress.vocabulary_id == vocabulary_id,
                )
            )
            assert progress is not None
            assert progress.status == "MASTERED"


def test_progress_summary_counts_unstudied_vocabulary_as_new() -> None:
    with TestClient(app) as client:
        user_id = create_client_user(client)
        baseline = client.get("/study/progress").json()
        first_id = add_vocabulary(user_id, "학교-progress-test", get_category_id("places"))
        add_vocabulary(user_id, "사과-progress-test", get_category_id("food"))
        headers = {"Origin": TRUSTED_ORIGIN}

        response = client.post(
            "/study/progress",
            json={"vocabulary_id": first_id, "result": "NOT_REMEMBERED"},
            headers=headers,
        )
        assert response.status_code == 200

        summary = client.get("/study/progress")
        assert summary.status_code == 200
        assert summary.json() == {
            "total": baseline["total"] + 2,
            "new": baseline["new"] + 1,
            "learning": baseline["learning"] + 1,
            "mastered": baseline["mastered"],
        }


def test_shared_seed_words_work_in_flashcards_with_private_user_progress() -> None:
    with TestClient(app) as learner, TestClient(app) as another_learner:
        learner_id = create_client_user(learner)
        another_learner_id = create_client_user(another_learner)
        food_id = get_category_id("food")

        learner_cards = learner.get(
            f"/study/cards?category_id={food_id}&level=BEGINNER&limit=5"
        ).json()
        another_cards = another_learner.get(
            f"/study/cards?category_id={food_id}&level=BEGINNER&limit=5"
        ).json()
        assert len(learner_cards) == 5
        assert len(another_cards) == 5
        assert all(card["example"] and card["example_en"] for card in learner_cards)

        vocabulary_id = learner_cards[0]["id"]
        headers = {"Origin": TRUSTED_ORIGIN}
        for client, result in ((learner, "REMEMBERED"), (another_learner, "NOT_REMEMBERED")):
            response = client.post(
                "/study/progress",
                json={"vocabulary_id": vocabulary_id, "result": result},
                headers=headers,
            )
            assert response.status_code == 200, response.text

        with SessionLocal() as session:
            vocabulary = session.get(Vocabulary, vocabulary_id)
            progress_rows = session.scalars(
                select(VocabularyProgress).where(
                    VocabularyProgress.vocabulary_id == vocabulary_id,
                    VocabularyProgress.user_id.in_([learner_id, another_learner_id]),
                )
            ).all()

        assert vocabulary is not None
        assert vocabulary.user_id is None
        assert {row.user_id for row in progress_rows} == {learner_id, another_learner_id}
        assert {row.remembered_count for row in progress_rows} == {0, 1}
        assert {row.not_remembered_count for row in progress_rows} == {0, 1}


def test_study_routes_require_authentication() -> None:
    with TestClient(app) as client:
        assert client.get("/study/cards").status_code == 401
        response = client.post(
            "/study/progress",
            json={"vocabulary_id": 1, "result": "REMEMBERED"},
            headers={"Origin": TRUSTED_ORIGIN},
        )
        assert response.status_code == 401