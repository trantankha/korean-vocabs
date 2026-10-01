from concurrent.futures import ThreadPoolExecutor
from itertools import cycle
from uuid import uuid4

import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from app.auth import create_access_token
from app.config import settings
from app.database import SessionLocal
from app.main import app
from app.models import Category, User, Vocabulary, VocabularyProgress

TRUSTED_ORIGIN = "http://127.0.0.1:3000"


@pytest.fixture(autouse=True)
def cleanup_quiz_test_users():
    yield
    with SessionLocal() as session:
        session.execute(delete(User).where(User.email.like("test-quiz-%@example.com")))
        session.commit()


def create_client_user(client: TestClient) -> int:
    email = f"test-quiz-{uuid4().hex}@example.com"
    with SessionLocal() as session:
        user = User(email=email, password_hash="unused-test-hash")
        session.add(user)
        session.commit()
        session.refresh(user)
        user_id = user.id
        token = create_access_token(user_id)
    client.cookies.set("korean_vocab_access", token)
    return user_id


def get_category_id(slug: str) -> int:
    with SessionLocal() as session:
        category_id = session.scalar(select(Category.id).where(Category.slug == slug))
    assert category_id is not None
    return category_id


def add_vocabulary(
    user_id: int,
    word: str,
    meaning: str,
    category_id: int,
    level: str = "ADVANCED",
    example: str | None = None,
    example_en: str | None = None,
) -> int:
    with SessionLocal() as session:
        vocabulary = Vocabulary(
            user_id=user_id,
            word=word,
            meaning=meaning,
            category_id=category_id,
            level=level,
            example=example,
            example_en=example_en,
        )
        session.add(vocabulary)
        session.commit()
        session.refresh(vocabulary)
        return vocabulary.id


def add_four_words(user_id: int, category_id: int) -> list[int]:
    return [
        add_vocabulary(
            user_id,
            "학교",
            "School",
            category_id,
            example="저는 학교에 가요.",
            example_en="I go to school.",
        ),
        add_vocabulary(user_id, "병원", "Hospital", category_id),
        add_vocabulary(user_id, "식당", "Restaurant", category_id),
        add_vocabulary(user_id, "공원", "Park", category_id),
    ]


def read_claims(question: dict) -> dict:
    return jwt.decode(
        question["question_token"],
        settings.secret_key.get_secret_value(),
        algorithms=["HS256"],
        issuer="korean-vocab-quiz",
    )


def correct_choice_id(question: dict) -> str:
    claims = read_claims(question)
    with SessionLocal() as session:
        vocabulary = session.get(Vocabulary, claims["vocabulary_id"])
    assert vocabulary is not None
    answer = (
        vocabulary.meaning
        if claims["direction"] == "KOREAN_TO_ENGLISH"
        else vocabulary.word
    )
    return next(choice_id for choice_id, text in claims["choices"].items() if text == answer)


def test_questions_use_only_owned_vocabulary_and_four_unique_choices() -> None:
    with TestClient(app) as client:
        user_id = create_client_user(client)
        with TestClient(app) as other_client:
            other_id = create_client_user(other_client)
        category_id = get_category_id("places")
        add_four_words(user_id, category_id)
        add_vocabulary(other_id, "교실", "Classroom", category_id, "ADVANCED")

        response = client.get(f"/quiz/questions?category_id={category_id}&level=ADVANCED&limit=5")

        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["matching_vocabulary"] == 4
        assert len(payload["questions"]) == 4
        for question in payload["questions"]:
            choice_texts = [choice["text"] for choice in question["choices"]]
            assert len(choice_texts) == 4
            assert len({text.casefold() for text in choice_texts}) == 4
            claims = read_claims(question)
            assert claims["sub"] == str(user_id)
            assert set(choice["id"] for choice in question["choices"]) == set(claims["choices"])
            assert all(text != "Classroom" and text != "교실" for text in choice_texts)


def test_quiz_can_mix_both_question_directions(monkeypatch: pytest.MonkeyPatch) -> None:
    with TestClient(app) as client:
        user_id = create_client_user(client)
        add_four_words(user_id, get_category_id("places"))
        direction_choices = cycle((lambda values: values[0], lambda values: values[-1]))
        monkeypatch.setattr("app.quiz.random.choice", lambda values: next(direction_choices)(values))

        questions = client.get("/quiz/questions?level=ADVANCED&limit=5").json()["questions"]

        assert {question["direction"] for question in questions} == {
            "KOREAN_TO_ENGLISH",
            "ENGLISH_TO_KOREAN",
        }


def test_answers_are_validated_server_side_and_update_shared_progress() -> None:
    with TestClient(app) as client:
        user_id = create_client_user(client)
        vocabulary_ids = add_four_words(user_id, get_category_id("places"))
        questions = client.get("/quiz/questions?level=ADVANCED&limit=5").json()["questions"]
        assert len(questions) == 4
        headers = {"Origin": TRUSTED_ORIGIN}
        example_question = next(
            question
            for question in questions
            if read_claims(question)["vocabulary_id"] == vocabulary_ids[0]
        )
        other_question = next(question for question in questions if question is not example_question)

        for question, expected_correct in zip(
            (example_question, other_question),
            (True, False),
            strict=True,
        ):
            claims = read_claims(question)
            expected_choice_id = correct_choice_id(question)
            selected_choice_id = (
                expected_choice_id
                if expected_correct
                else next(choice["id"] for choice in question["choices"] if choice["id"] != expected_choice_id)
            )
            answer = client.post(
                "/quiz/answer",
                json={
                    "question_token": question["question_token"],
                    "selected_choice_id": selected_choice_id,
                },
                headers=headers,
            )

            assert answer.status_code == 200, answer.text
            result = answer.json()
            assert result["correct"] is expected_correct
            assert result["correct_answer"] in [choice["text"] for choice in question["choices"]]
            if expected_correct:
                assert result["selected_answer"] == result["correct_answer"]
                assert result["example"] == "저는 학교에 가요."
                assert result["example_en"] == "I go to school."
            else:
                assert result["selected_answer"] != result["correct_answer"]

            replay = client.post(
                "/quiz/answer",
                json={
                    "question_token": question["question_token"],
                    "selected_choice_id": selected_choice_id,
                },
                headers=headers,
            )
            assert replay.status_code == 200
            assert replay.json() == result

            with SessionLocal() as session:
                progress = session.scalar(
                    select(VocabularyProgress).where(
                        VocabularyProgress.user_id == user_id,
                        VocabularyProgress.vocabulary_id == claims["vocabulary_id"],
                    )
                )
                assert progress is not None
                assert progress.review_count == 1
                assert progress.remembered_count == int(expected_correct)
                assert progress.not_remembered_count == int(not expected_correct)

        claims = read_claims(other_question)
        original_choice_id = correct_choice_id(other_question)
        changed_answer = client.post(
            "/quiz/answer",
            json={
                "question_token": other_question["question_token"],
                "selected_choice_id": original_choice_id,
            },
            headers=headers,
        )
        assert changed_answer.status_code == 409
        with SessionLocal() as session:
            progress = session.scalar(
                select(VocabularyProgress).where(
                    VocabularyProgress.user_id == user_id,
                    VocabularyProgress.vocabulary_id == claims["vocabulary_id"],
                )
            )
            assert progress is not None
            assert progress.review_count == 1
            assert progress.not_remembered_count == 1

        assert len(vocabulary_ids) == 4


def test_user_cannot_answer_another_users_question() -> None:
    with TestClient(app) as owner, TestClient(app) as other_user:
        owner_id = create_client_user(owner)
        create_client_user(other_user)
        add_four_words(owner_id, get_category_id("places"))
        question = owner.get("/quiz/questions?level=ADVANCED&limit=5").json()["questions"][0]
        choice_id = question["choices"][0]["id"]

        response = other_user.post(
            "/quiz/answer",
            json={"question_token": question["question_token"], "selected_choice_id": choice_id},
            headers={"Origin": TRUSTED_ORIGIN},
        )

        assert response.status_code == 404


def test_concurrent_duplicate_answers_update_progress_once() -> None:
    with TestClient(app) as question_client:
        user_id = create_client_user(question_client)
        vocabulary_ids = add_four_words(user_id, get_category_id("places"))
        question = question_client.get("/quiz/questions?level=ADVANCED&limit=5").json()["questions"][0]
        selected_choice_id = correct_choice_id(question)
        token = create_access_token(user_id)
        payload = {
            "question_token": question["question_token"],
            "selected_choice_id": selected_choice_id,
        }
        headers = {"Origin": TRUSTED_ORIGIN}
        with TestClient(app) as first_client, TestClient(app) as second_client:
            first_client.cookies.set("korean_vocab_access", token)
            second_client.cookies.set("korean_vocab_access", token)
            with ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(first_client.post, "/quiz/answer", json=payload, headers=headers)
                second = executor.submit(second_client.post, "/quiz/answer", json=payload, headers=headers)
                responses = (first.result(), second.result())

        assert [response.status_code for response in responses] == [200, 200]
        assert responses[0].json() == responses[1].json()
        claims = read_claims(question)
        with SessionLocal() as session:
            progress = session.scalar(
                select(VocabularyProgress).where(
                    VocabularyProgress.user_id == user_id,
                    VocabularyProgress.vocabulary_id == claims["vocabulary_id"],
                )
            )
            assert progress is not None
            assert progress.review_count == 1
        assert len(vocabulary_ids) == 4


def test_invalid_token_and_choice_are_rejected() -> None:
    with TestClient(app) as client:
        user_id = create_client_user(client)
        add_four_words(user_id, get_category_id("places"))
        question = client.get("/quiz/questions?level=ADVANCED&limit=5").json()["questions"][0]
        headers = {"Origin": TRUSTED_ORIGIN}

        invalid_token = client.post(
            "/quiz/answer",
            json={"question_token": "invalid-token", "selected_choice_id": question["choices"][0]["id"]},
            headers=headers,
        )
        invalid_choice = client.post(
            "/quiz/answer",
            json={"question_token": question["question_token"], "selected_choice_id": "not-an-option"},
            headers=headers,
        )

        assert invalid_token.status_code == 400
        assert invalid_choice.status_code == 422


def test_quiz_reports_no_matches_and_insufficient_choices(monkeypatch: pytest.MonkeyPatch) -> None:
    with TestClient(app) as empty_client:
        create_client_user(empty_client)
        empty = empty_client.get("/quiz/questions?level=ADVANCED&limit=5").json()
        assert empty["questions"] == []
        assert empty["limitation"] == "NO_MATCHING_VOCABULARY"

    with TestClient(app) as limited_client:
        create_client_user(limited_client)
        monkeypatch.setattr("app.quiz._make_question", lambda *args: None)
        insufficient = limited_client.get("/quiz/questions?limit=5").json()
        assert insufficient["questions"] == []
        assert insufficient["limitation"] == "INSUFFICIENT_CHOICES"


def test_shared_seed_words_work_in_english_quiz_and_record_progress() -> None:
    with TestClient(app) as client:
        user_id = create_client_user(client)
        food_id = get_category_id("food")

        payload = client.get(
            f"/quiz/questions?category_id={food_id}&level=BEGINNER&limit=5"
        ).json()
        assert len(payload["questions"]) == 5
        question = payload["questions"][0]
        claims = read_claims(question)
        selected_choice_id = correct_choice_id(question)
        response = client.post(
            "/quiz/answer",
            json={
                "question_token": question["question_token"],
                "selected_choice_id": selected_choice_id,
            },
            headers={"Origin": TRUSTED_ORIGIN},
        )

        assert response.status_code == 200, response.text
        result = response.json()
        assert result["correct"] is True
        assert result["example"]
        assert result["example_en"]
        with SessionLocal() as session:
            vocabulary = session.get(Vocabulary, claims["vocabulary_id"])
            progress = session.scalar(
                select(VocabularyProgress).where(
                    VocabularyProgress.user_id == user_id,
                    VocabularyProgress.vocabulary_id == claims["vocabulary_id"],
                )
            )

        assert vocabulary is not None
        assert vocabulary.user_id is None
        assert progress is not None
        assert progress.remembered_count == 1


def test_quiz_routes_require_authentication() -> None:
    with TestClient(app) as client:
        assert client.get("/quiz/questions").status_code == 401
        response = client.post(
            "/quiz/answer",
            json={"question_token": "token", "selected_choice_id": "choice"},
            headers={"Origin": TRUSTED_ORIGIN},
        )
        assert response.status_code == 401