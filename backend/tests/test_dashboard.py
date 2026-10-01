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
        session.commit()
        session.refresh(user)
        places_id = session.scalar(select(Category.id).where(Category.slug == "places"))
        food_id = session.scalar(select(Category.id).where(Category.slug == "food"))
        assert places_id is not None
        assert food_id is not None
        token = create_access_token(user.id)

    with TestClient(app) as client:
        client.cookies.set("korean_vocab_access", token)
        baseline = client.get("/dashboard/stats").json()
        suffix = uuid4().hex[:8]
        with SessionLocal() as session:
            session.add_all(
                [
                    Vocabulary(user_id=user.id, word=f"학교{suffix}", meaning="School", category_id=places_id, level="BEGINNER"),
                    Vocabulary(user_id=user.id, word=f"도서관{suffix}", meaning="Library", category_id=places_id, level="BEGINNER"),
                    Vocabulary(user_id=user.id, word=f"김치{suffix}", meaning="Kimchi", category_id=food_id, level="ADVANCED"),
                ]
            )
            session.commit()
        response = client.get("/dashboard/stats")

    assert response.status_code == 200
    stats = response.json()
    assert stats["total_vocabulary"] == baseline["total_vocabulary"] + 3
    baseline_levels = {item["level"]: item["count"] for item in baseline["by_level"]}
    assert stats["by_level"] == [
        {"level": "BEGINNER", "count": baseline_levels["BEGINNER"] + 2},
        {"level": "INTERMEDIATE", "count": baseline_levels["INTERMEDIATE"]},
        {"level": "ADVANCED", "count": baseline_levels["ADVANCED"] + 1},
    ]
    baseline_categories = {item["slug"]: item["count"] for item in baseline["by_category"]}
    expected_categories = dict(baseline_categories)
    expected_categories["places"] = expected_categories.get("places", 0) + 2
    expected_categories["food"] = expected_categories.get("food", 0) + 1
    assert stats["categories_used"] == len(expected_categories)
    assert {category["slug"]: category["count"] for category in stats["by_category"]} == expected_categories

    with SessionLocal() as session:
        test_user = session.scalar(select(User).where(User.email == email))
        assert test_user is not None
        session.delete(test_user)
        session.commit()


def test_dashboard_stats_require_authentication() -> None:
    with TestClient(app) as client:
        response = client.get("/dashboard/stats")

    assert response.status_code == 401