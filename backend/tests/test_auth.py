from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.auth import password_hasher
from app.database import SessionLocal
from app.main import app
from app.models import User

TRUSTED_ORIGIN = "http://127.0.0.1:3000"


@pytest.fixture(autouse=True)
def cleanup_auth_test_users():
    yield
    with SessionLocal() as session:
        session.execute(delete(User).where(User.email.like("test-auth-%@example.com")))
        session.commit()


def test_register_login_current_user_and_logout() -> None:
    email = f"test-auth-{uuid4().hex}@example.com"
    password = "correct-horse-123"
    headers = {"Origin": TRUSTED_ORIGIN}

    with TestClient(app) as client:
        registered = client.post(
            "/auth/register",
            json={"email": email, "password": password},
            headers=headers,
        )

        assert registered.status_code == 201
        assert registered.json()["email"] == email
        assert "password_hash" not in registered.json()

        cookie = registered.headers["set-cookie"].lower()
        assert "httponly" in cookie
        assert "samesite=lax" in cookie
        assert "max-age=3600" in cookie

        with SessionLocal() as session:
            user = session.scalar(select(User).where(User.email == email))
            assert user is not None
            assert user.password_hash != password
            assert password_hasher.verify(password, user.password_hash)

        assert client.get("/auth/me").json()["email"] == email
        assert client.post("/auth/logout", headers=headers).status_code == 204
        assert client.get("/auth/me").status_code == 401

        wrong_password = client.post(
            "/auth/login",
            json={"email": email, "password": "incorrect-password"},
            headers=headers,
        )
        assert wrong_password.status_code == 401

        logged_in = client.post(
            "/auth/login",
            json={"email": email, "password": password},
            headers=headers,
        )
        assert logged_in.status_code == 200
        assert client.get("/auth/me").status_code == 200


def test_duplicate_email_is_rejected() -> None:
    email = f"test-auth-{uuid4().hex}@example.com"
    payload = {"email": email, "password": "correct-horse-123"}
    headers = {"Origin": TRUSTED_ORIGIN}

    with TestClient(app) as client:
        assert client.post("/auth/register", json=payload, headers=headers).status_code == 201
        duplicate = client.post("/auth/register", json=payload, headers=headers)

    assert duplicate.status_code == 409


@pytest.mark.parametrize("origin", [None, "https://untrusted.example"])
def test_untrusted_or_missing_origin_cannot_register(origin: str | None) -> None:
    email = f"test-auth-{uuid4().hex}@example.com"
    headers = {} if origin is None else {"Origin": origin}

    with TestClient(app) as client:
        response = client.post(
            "/auth/register",
            json={"email": email, "password": "correct-horse-123"},
            headers=headers,
        )

    assert response.status_code == 403
    with SessionLocal() as session:
        assert session.scalar(select(User.id).where(User.email == email)) is None