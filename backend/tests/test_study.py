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
        owned_id = add_vocabulary(owner_id, "학교", places_id, "BEGINNER")
        add_vocabulary(owner_id, "사과", food_id, "INTERMEDIATE")
        add_vocabulary(other_id, "집", places_id, "BEGINNER")

        response = owner.get(
            "/study/cards?category_id="
            f"{places_id}&level=BEGINNER&limit=5"
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
        first_id = add_vocabulary(user_id, "학교", get_category_id("places"))
        add_vocabulary(user_id, "사과", get_category_id("food"))
        headers = {"Origin": TRUSTED_ORIGIN}

        response = client.post(
            "/study/progress",
            json={"vocabulary_id": first_id, "result": "NOT_REMEMBERED"},
            headers=headers,
        )
        assert response.status_code == 200

        summary = client.get("/study/progress")
        assert summary.status_code == 200
        assert summary.json() == {"total": 2, "new": 1, "learning": 1, "mastered": 0}


def test_study_routes_require_authentication() -> None:
    with TestClient(app) as client:
        assert client.get("/study/cards").status_code == 401
        response = client.post(
            "/study/progress",
            json={"vocabulary_id": 1, "result": "REMEMBERED"},
            headers={"Origin": TRUSTED_ORIGIN},
        )
        assert response.status_code == 401