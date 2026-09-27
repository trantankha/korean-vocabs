from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth import create_access_token
from app.database import SessionLocal
from app.main import app
from app.models import Category, User, Vocabulary


def test_dashboard_stats_are_scoped_and_include_empty_levels() -> None:
    email = f"test-dashboard-{uuid4().hex}@example.com"
    with SessionLocal() as session:
        user = User(email=email, password_hash="unused-test-hash")
        session.add(user)
        session.flush()
        places_id = session.scalar(select(Category.id).where(Category.slug == "places"))
        food_id = session.scalar(select(Category.id).where(Category.slug == "food"))
        assert places_id is not None
        assert food_id is not None
        session.add_all(
            [
                Vocabulary(user_id=user.id, word="학교", meaning="School", category_id=places_id, level="BEGINNER"),
                Vocabulary(user_id=user.id, word="도서관", meaning="Library", category_id=places_id, level="BEGINNER"),
                Vocabulary(user_id=user.id, word="김치", meaning="Kimchi", category_id=food_id, level="ADVANCED"),
            ]
        )
        session.commit()
        token = create_access_token(user.id)

    with TestClient(app) as client:
        client.cookies.set("korean_vocab_access", token)
        response = client.get("/dashboard/stats")

    assert response.status_code == 200
    stats = response.json()
    assert stats["total_vocabulary"] == 3
    assert stats["by_level"] == [
        {"level": "BEGINNER", "count": 2},
        {"level": "INTERMEDIATE", "count": 0},
        {"level": "ADVANCED", "count": 1},
    ]
    assert stats["categories_used"] == 2
    assert [(category["slug"], category["count"]) for category in stats["by_category"]] == [
        ("places", 2),
        ("food", 1),
    ]

    with SessionLocal() as session:
        test_user = session.scalar(select(User).where(User.email == email))
        assert test_user is not None
        session.delete(test_user)
        session.commit()


def test_dashboard_stats_require_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/dashboard/stats")

    assert response.status_code == 401