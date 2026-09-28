from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import random
import secrets
from typing import Literal

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, status
from jwt import InvalidTokenError
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.config import settings
from app.database import get_db
from app.learning_progress import record_learning_result
from app.models import QuizAnswerReceipt, User, Vocabulary

router = APIRouter(prefix="/quiz", tags=["quiz"])
VocabularyLevel = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]
QuizDirection = Literal["KOREAN_TO_VIETNAMESE", "VIETNAMESE_TO_KOREAN"]
QuizLimitation = Literal[
    "NO_VOCABULARY",
    "NO_MATCHING_VOCABULARY",
    "INSUFFICIENT_CHOICES",
]
TOKEN_ISSUER = "korean-vocab-quiz"
TOKEN_LIFETIME = timedelta(hours=2)
RECEIPT_RETENTION = TOKEN_LIFETIME + timedelta(minutes=5)


class QuizChoice(BaseModel):
    id: str
    text: str


class QuizQuestion(BaseModel):
    question_token: str
    direction: QuizDirection
    prompt: str
    choices: list[QuizChoice]


class QuizQuestionSet(BaseModel):
    questions: list[QuizQuestion]
    requested: int
    matching_vocabulary: int
    available: int
    limitation: QuizLimitation | None


class QuizAnswerInput(BaseModel):
    question_token: str = Field(min_length=1, max_length=30000)
    selected_choice_id: str = Field(min_length=1, max_length=32)


class QuizAnswerResponse(BaseModel):
    correct: bool
    selected_answer: str
    correct_answer: str
    example: str | None


def _answer_text(vocabulary: Vocabulary, direction: QuizDirection) -> str:
    return vocabulary.meaning if direction == "KOREAN_TO_VIETNAMESE" else vocabulary.word


def _answer_digest(user_id: int, vocabulary_id: int, direction: str, answer: str) -> str:
    message = f"{user_id}:{vocabulary_id}:{direction}:{answer.strip().casefold()}"
    return hmac.new(
        settings.secret_key.get_secret_value().encode(),
        message.encode(),
        hashlib.sha256,
    ).hexdigest()


def _receipt_response(receipt: QuizAnswerReceipt) -> QuizAnswerResponse:
    return QuizAnswerResponse(
        correct=receipt.correct,
        selected_answer=receipt.selected_answer,
        correct_answer=receipt.correct_answer,
        example=receipt.example,
    )


def _select_choices(
    target: Vocabulary,
    vocabulary: list[Vocabulary],
    direction: QuizDirection,
) -> list[QuizChoice] | None:
    correct_answer = _answer_text(target, direction).strip()
    if not correct_answer:
        return None

    choices = [QuizChoice(id=secrets.token_urlsafe(9), text=correct_answer)]
    seen = {correct_answer.casefold()}
    same_category_and_level = [
        item
        for item in vocabulary
        if item.id != target.id
        and item.category_id == target.category_id
        and item.level == target.level
    ]
    same_level = [
        item
        for item in vocabulary
        if item.id != target.id
        and item.level == target.level
        and item.category_id != target.category_id
    ]
    any_vocabulary = [
        item
        for item in vocabulary
        if item.id != target.id and item.level != target.level
    ]

    for tier in (same_category_and_level, same_level, any_vocabulary):
        random.shuffle(tier)
        for candidate in tier:
            text = _answer_text(candidate, direction).strip()
            normalized = text.casefold()
            if not text or normalized in seen:
                continue
            seen.add(normalized)
            choices.append(QuizChoice(id=secrets.token_urlsafe(9), text=text))
            if len(choices) == 4:
                random.shuffle(choices)
                return choices

    return None


def _make_question(
    user_id: int,
    target: Vocabulary,
    vocabulary: list[Vocabulary],
) -> QuizQuestion | None:
    candidates: list[tuple[QuizDirection, list[QuizChoice]]] = []
    for direction in ("KOREAN_TO_VIETNAMESE", "VIETNAMESE_TO_KOREAN"):
        choices = _select_choices(target, vocabulary, direction)
        if choices is not None:
            candidates.append((direction, choices))
    if not candidates:
        return None

    direction, choices = random.choice(candidates)
    prompt = (
        f'What does "{target.word}" mean?'
        if direction == "KOREAN_TO_VIETNAMESE"
        else f'How do you say "{target.meaning}" in Korean?'
    )
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "iss": TOKEN_ISSUER,
            "sub": str(user_id),
            "purpose": "quiz-answer",
            "jti": secrets.token_urlsafe(24),
            "vocabulary_id": target.id,
            "direction": direction,
            "answer_digest": _answer_digest(
                user_id,
                target.id,
                direction,
                _answer_text(target, direction),
            ),
            "choices": {choice.id: choice.text for choice in choices},
            "iat": now,
            "exp": now + TOKEN_LIFETIME,
        },
        settings.secret_key.get_secret_value(),
        algorithm="HS256",
    )
    return QuizQuestion(
        question_token=token,
        direction=direction,
        prompt=prompt,
        choices=choices,
    )


@router.get("/questions", response_model=QuizQuestionSet)
def get_quiz_questions(
    category_id: int | None = Query(default=None, ge=1),
    level: VocabularyLevel | None = None,
    limit: int = Query(default=10, ge=1, le=20),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> QuizQuestionSet:
    if limit not in {5, 10, 20}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="limit must be 5, 10, or 20",
        )

    vocabulary = list(
        session.scalars(
            select(Vocabulary).where(Vocabulary.user_id == user.id)
        ).all()
    )
    matching = [
        item
        for item in vocabulary
        if (category_id is None or item.category_id == category_id)
        and (level is None or item.level == level)
    ]
    random.shuffle(matching)
    usable_questions = [
        question
        for item in matching
        if (question := _make_question(user.id, item, vocabulary)) is not None
    ]
    random.shuffle(usable_questions)
    selected_questions = usable_questions[:limit]

    limitation: QuizLimitation | None = None
    if not vocabulary:
        limitation = "NO_VOCABULARY"
    elif not matching:
        limitation = "NO_MATCHING_VOCABULARY"
    elif len(usable_questions) < min(limit, len(matching)):
        limitation = "INSUFFICIENT_CHOICES"

    return QuizQuestionSet(
        questions=selected_questions,
        requested=limit,
        matching_vocabulary=len(matching),
        available=len(usable_questions),
        limitation=limitation,
    )


@router.post("/answer", response_model=QuizAnswerResponse)
def submit_quiz_answer(
    answer_input: QuizAnswerInput,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> QuizAnswerResponse:
    try:
        claims = jwt.decode(
            answer_input.question_token,
            settings.secret_key.get_secret_value(),
            algorithms=["HS256"],
            issuer=TOKEN_ISSUER,
        )
    except (InvalidTokenError, TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Quiz question is invalid or expired",
        ) from None

    if claims.get("purpose") != "quiz-answer":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quiz question")
    if claims.get("sub") != str(user.id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz question not found")

    vocabulary_id = claims.get("vocabulary_id")
    direction = claims.get("direction")
    token_id = claims.get("jti")
    choices = claims.get("choices")
    answer_digest = claims.get("answer_digest")
    if (
        not isinstance(token_id, str)
        or not token_id
        or len(token_id) > 64
        or not token_id.isascii()
        or not isinstance(vocabulary_id, int)
        or isinstance(vocabulary_id, bool)
        or direction not in {"KOREAN_TO_VIETNAMESE", "VIETNAMESE_TO_KOREAN"}
        or not isinstance(choices, dict)
        or len(choices) != 4
        or not isinstance(answer_digest, str)
        or len(answer_digest) != 64
        or any(not isinstance(choice_id, str) or not isinstance(text, str) for choice_id, text in choices.items())
        or len({text.strip().casefold() for text in choices.values()}) != 4
    ):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid quiz question")

    selected_answer = choices.get(answer_input.selected_choice_id)
    if selected_answer is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Selected answer is not one of the question choices",
        )

    session.execute(
        delete(QuizAnswerReceipt).where(
            QuizAnswerReceipt.created_at < datetime.now(timezone.utc) - RECEIPT_RETENTION
        )
    )
    prior_receipt = session.get(QuizAnswerReceipt, token_id)
    if prior_receipt is not None:
        if prior_receipt.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz question not found")
        if prior_receipt.selected_choice_id != answer_input.selected_choice_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This quiz question has already been answered",
            )
        return _receipt_response(prior_receipt)

    vocabulary_item = session.scalar(
        select(Vocabulary).where(
            Vocabulary.id == vocabulary_id,
            Vocabulary.user_id == user.id,
        )
    )
    if vocabulary_item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz question not found")

    correct_answer = _answer_text(vocabulary_item, direction).strip()
    expected_digest = _answer_digest(user.id, vocabulary_item.id, direction, correct_answer)
    if not hmac.compare_digest(answer_digest, expected_digest):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Vocabulary changed after this question was created",
        )

    selected_digest = _answer_digest(
        user.id,
        vocabulary_item.id,
        direction,
        selected_answer,
    )
    correct = hmac.compare_digest(selected_digest, answer_digest)
    record_learning_result(
        session,
        user_id=user.id,
        vocabulary_id=vocabulary_item.id,
        remembered=correct,
    )
    receipt = QuizAnswerReceipt(
        token_id=token_id,
        user_id=user.id,
        vocabulary_id=vocabulary_item.id,
        selected_choice_id=answer_input.selected_choice_id,
        correct=correct,
        selected_answer=selected_answer,
        correct_answer=correct_answer,
        example=vocabulary_item.example,
    )
    session.add(receipt)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        prior_receipt = session.get(QuizAnswerReceipt, token_id)
        if prior_receipt is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Quiz answer could not be recorded; please retry",
            ) from None
        if prior_receipt.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz question not found") from None
        if prior_receipt.selected_choice_id != answer_input.selected_choice_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="This quiz question has already been answered",
            ) from None
        return _receipt_response(prior_receipt)

    return _receipt_response(receipt)