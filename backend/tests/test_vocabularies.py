from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.auth import create_access_token
from app.database import SessionLocal
from app.main import app
from app.models import Category, User, Vocabulary

TRUSTED_ORIGIN = "http://127.0.0.1:3000"
SHARED_TEST_VOCABULARY_IDS: list[int] = []


@pytest.fixture(autouse=True)
def cleanup_vocabulary_test_users():
    yield
    with SessionLocal() as session:
        if SHARED_TEST_VOCABULARY_IDS:
            session.execute(
                delete(Vocabulary).where(Vocabulary.id.in_(SHARED_TEST_VOCABULARY_IDS))
            )
            SHARED_TEST_VOCABULARY_IDS.clear()
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
        "example_en": "",
        "category_id": category_id,
        "level": level,
    }


def test_vocabulary_crud_search_filter_and_pagination() -> None:
    with TestClient(app) as client:
        make_authenticated_client(client)
        headers = {"Origin": TRUSTED_ORIGIN}
        places_id = get_category_id("places")
        food_id = get_category_id("food")
        initial_total = client.get("/vocabularies").json()["total"]
        suffix = uuid4().hex[:8]
        school_word = f"학교{suffix}"
        apple_word = f"사과{suffix}"

        created = client.post(
            "/vocabularies",
            json=make_vocabulary(f" {school_word} ", " School ", places_id),
            headers=headers,
        )
        assert created.status_code == 201, created.text
        item = created.json()
        assert item["word"] == school_word
        assert item["meaning"] == "School"
        assert item["example"] is None
        assert item["is_shared"] is False
        assert "user_id" not in item
        assert item["category"]["slug"] == "places"

        detail = client.get(f"/vocabularies/{item['id']}")
        assert detail.status_code == 200
        assert detail.json()["id"] == item["id"]

        updated = client.put(
            f"/vocabularies/{item['id']}",
            json=make_vocabulary(f" {school_word} ", "Academy", places_id, "INTERMEDIATE"),
            headers=headers,
        )
        assert updated.status_code == 200
        assert updated.json()["level"] == "INTERMEDIATE"

        client.post(
            "/vocabularies",
            json=make_vocabulary(apple_word, "Apple", food_id),
            headers=headers,
        )
        filtered = client.get(
            "/vocabularies?search=Academy&category_id="
            f"{places_id}&level=INTERMEDIATE&page=1&limit=1"
        )
        assert filtered.status_code == 200
        assert filtered.json()["total"] == 1
        assert filtered.json()["items"][0]["meaning"] == "Academy"

        korean_search = client.get(f"/vocabularies?search={school_word}")
        assert korean_search.json()["total"] == 1
        assert korean_search.json()["items"][0]["word"] == school_word

        paged = client.get("/vocabularies?page=1&limit=1&sort=created_at_desc")
        assert paged.json()["limit"] == 1
        assert paged.json()["total"] == initial_total + 2
        assert paged.json()["total_pages"] == (initial_total + 2 + 0) // 1

        deleted = client.delete(f"/vocabularies/{item['id']}", headers=headers)
        assert deleted.status_code == 204
        assert client.get(f"/vocabularies/{item['id']}").status_code == 404
        assert client.get("/vocabularies").json()["total"] == initial_total + 1


def test_vocabulary_access_is_scoped_to_authenticated_user() -> None:
    with TestClient(app) as owner, TestClient(app) as other_user:
        make_authenticated_client(owner)
        make_authenticated_client(other_user)
        other_baseline = other_user.get("/vocabularies").json()["total"]
        headers = {"Origin": TRUSTED_ORIGIN}
        vocabulary = owner.post(
            "/vocabularies",
            json=make_vocabulary(f"private-{uuid4().hex[:8]}", "Private word", get_category_id("places")),
            headers=headers,
        ).json()
        vocabulary_id = vocabulary["id"]

        assert other_user.get("/vocabularies").json()["total"] == other_baseline
        assert vocabulary_id not in {item["id"] for item in other_user.get("/vocabularies").json()["items"]}
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
        assert len(client.get("/categories").json()) == 10
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


def test_shared_vocabulary_is_visible_but_not_editable_and_personal_entry_overrides_duplicate() -> None:
    with TestClient(app) as owner, TestClient(app) as other_user:
        make_authenticated_client(owner)
        make_authenticated_client(other_user)
        headers = {"Origin": TRUSTED_ORIGIN}
        places_id = get_category_id("places")
        suffix = uuid4().hex[:8]
        shared_word_text = f"공유테스트{suffix}"
        shared_book_text = f"공유책{suffix}"
        owner_baseline = owner.get("/vocabularies").json()["total"]
        other_baseline = other_user.get("/vocabularies").json()["total"]
        with SessionLocal() as session:
            shared_word = Vocabulary(
                user_id=None,
            word=shared_word_text,
                meaning="school",
                example="저는 학교에 가요.",
                example_en="I go to school.",
                category_id=places_id,
                level="BEGINNER",
            )
            shared_book = Vocabulary(
                user_id=None,
                word=shared_book_text,
                meaning="book",
                category_id=places_id,
                level="BEGINNER",
            )
            session.add_all([shared_word, shared_book])
            session.commit()
            shared_word_id = shared_word.id
            shared_book_id = shared_book.id
            SHARED_TEST_VOCABULARY_IDS.extend([shared_word_id, shared_book_id])

        personal = owner.post(
            "/vocabularies",
            json=make_vocabulary(f" {shared_word_text} ", "personal meaning", places_id),
            headers=headers,
        )
        assert personal.status_code == 201, personal.text
        personal_id = personal.json()["id"]

        owner_list = owner.get("/vocabularies").json()
        other_list = other_user.get("/vocabularies").json()
        assert owner_list["total"] == owner_baseline + 2
        assert personal_id in {item["id"] for item in owner_list["items"]}
        assert shared_book_id in {item["id"] for item in owner_list["items"]}
        assert shared_word_id not in {item["id"] for item in owner_list["items"]}
        assert next(item for item in owner_list["items"] if item["id"] == shared_book_id)["is_shared"] is True
        assert other_list["total"] == other_baseline + 2
        assert {shared_word_id, shared_book_id} <= {item["id"] for item in other_list["items"]}
        assert owner.get(f"/vocabularies/{shared_book_id}").status_code == 200
        assert other_user.get(f"/vocabularies/{shared_book_id}").status_code == 200
        assert owner.get(f"/vocabularies/{shared_word_id}").status_code == 404
        assert owner.put(
            f"/vocabularies/{shared_book_id}",
            json=make_vocabulary(shared_book_text, "modified", places_id),
            headers=headers,
        ).status_code == 404
        assert owner.delete(f"/vocabularies/{shared_book_id}", headers=headers).status_code == 404


def test_vocabulary_routes_require_authentication() -> None:
    with TestClient(app) as client:
        headers = {"Origin": TRUSTED_ORIGIN}
        payload = make_vocabulary("학교", "School", get_category_id("places"))
        assert client.get("/vocabularies").status_code == 401
        assert client.post("/vocabularies", json=payload, headers=headers).status_code == 401