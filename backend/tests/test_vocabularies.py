from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.auth import create_access_token
from app.database import SessionLocal
from app.main import app
from app.models import Category, User, Vocabulary

TRUSTED_ORIGIN = "http://127.0.0.1:3000"


@pytest.fixture(autouse=True)
def cleanup_vocabulary_test_users():
    yield
    with SessionLocal() as session:
        session.execute(delete(User).where(User.email.like("test-vocabulary-%@example.com")))
        session.commit()


def make_authenticated_client(client: TestClient) -> str:
    email = f"test-vocabulary-{uuid4().hex}@example.com"
    with SessionLocal() as session:
        user = User(email=email, password_hash="unused-test-hash")
        session.add(user)
        session.commit()
        session.refresh(user)
        token = create_access_token(user.id)
    client.cookies.set("korean_vocab_access", token)
    return email


def get_category_id(slug: str) -> int:
    with SessionLocal() as session:
        category_id = session.scalar(select(Category.id).where(Category.slug == slug))
    assert category_id is not None
    return category_id


def make_vocabulary(word: str, meaning: str, category_id: int, level: str = "BEGINNER") -> dict:
    return {
        "word": word,
        "meaning": meaning,
        "example": "",
        "category_id": category_id,
        "level": level,
    }


def test_vocabulary_crud_search_filter_and_pagination() -> None:
    with TestClient(app) as client:
        make_authenticated_client(client)
        headers = {"Origin": TRUSTED_ORIGIN}
        places_id = get_category_id("places")
        food_id = get_category_id("food")

        created = client.post(
            "/vocabularies",
            json=make_vocabulary(" 학교 ", " Trường học ", places_id),
            headers=headers,
        )
        assert created.status_code == 201, created.text
        item = created.json()
        assert item["word"] == "학교"
        assert item["meaning"] == "Trường học"
        assert item["example"] is None
        assert item["category"]["slug"] == "places"

        detail = client.get(f"/vocabularies/{item['id']}")
        assert detail.status_code == 200
        assert detail.json()["id"] == item["id"]

        updated = client.put(
            f"/vocabularies/{item['id']}",
            json=make_vocabulary(" 학교 ", "Academy", places_id, "INTERMEDIATE"),
            headers=headers,
        )
        assert updated.status_code == 200
        assert updated.json()["level"] == "INTERMEDIATE"

        client.post(
            "/vocabularies",
            json=make_vocabulary("사과", "Apple", food_id),
            headers=headers,
        )
        filtered = client.get(
            "/vocabularies?search=Academy&category_id="
            f"{places_id}&level=INTERMEDIATE&page=1&limit=1"
        )
        assert filtered.status_code == 200
        assert filtered.json()["total"] == 1
        assert filtered.json()["items"][0]["meaning"] == "Academy"

        korean_search = client.get("/vocabularies?search=학교")
        assert korean_search.json()["total"] == 1
        assert korean_search.json()["items"][0]["word"] == "학교"

        paged = client.get("/vocabularies?page=1&limit=1&sort=created_at_desc")
        assert paged.json()["limit"] == 1
        assert paged.json()["total"] == 2
        assert paged.json()["total_pages"] == 2

        deleted = client.delete(f"/vocabularies/{item['id']}", headers=headers)
        assert deleted.status_code == 204
        assert client.get(f"/vocabularies/{item['id']}").status_code == 404


def test_vocabulary_access_is_scoped_to_authenticated_user() -> None:
    with TestClient(app) as owner, TestClient(app) as other_user:
        make_authenticated_client(owner)
        make_authenticated_client(other_user)
        headers = {"Origin": TRUSTED_ORIGIN}
        vocabulary = owner.post(
            "/vocabularies",
            json=make_vocabulary("학교", "School", get_category_id("places")),
            headers=headers,
        ).json()
        vocabulary_id = vocabulary["id"]

        assert other_user.get("/vocabularies").json()["total"] == 0
        assert other_user.get(f"/vocabularies/{vocabulary_id}").status_code == 404
        assert other_user.put(
            f"/vocabularies/{vocabulary_id}",
            json=make_vocabulary("침해", "Modified", get_category_id("places")),
            headers=headers,
        ).status_code == 404
        assert other_user.delete(f"/vocabularies/{vocabulary_id}", headers=headers).status_code == 404
        assert owner.get(f"/vocabularies/{vocabulary_id}").status_code == 200


def test_categories_and_validation() -> None:
    with TestClient(app) as client:
        assert len(client.get("/categories").json()) == 6
        make_authenticated_client(client)
        headers = {"Origin": TRUSTED_ORIGIN}

        empty_word = client.post(
            "/vocabularies",
            json=make_vocabulary("   ", "Meaning", get_category_id("places")),
            headers=headers,
        )
        assert empty_word.status_code == 422

        invalid_level = client.post(
            "/vocabularies",
            json=make_vocabulary("학교", "School", get_category_id("places"), "EXPERT"),
            headers=headers,
        )
        assert invalid_level.status_code == 422

        invalid_category = client.post(
            "/vocabularies",
            json=make_vocabulary("학교", "School", 999999),
            headers=headers,
        )
        assert invalid_category.status_code == 422


def test_vocabulary_routes_require_authentication() -> None:
    with TestClient(app) as client:
        headers = {"Origin": TRUSTED_ORIGIN}
        payload = make_vocabulary("학교", "School", get_category_id("places"))
        assert client.get("/vocabularies").status_code == 401
        assert client.post("/vocabularies", json=payload, headers=headers).status_code == 401