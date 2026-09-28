from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.learning_progress import record_learning_result
from app.models import User, Vocabulary, VocabularyProgress

router = APIRouter(prefix="/study", tags=["study"])
VocabularyLevel = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]
StudyResult = Literal["REMEMBERED", "NOT_REMEMBERED"]
ProgressStatus = Literal["NEW", "LEARNING", "MASTERED"]


class StudyCard(BaseModel):
    id: int
    word: str
    meaning: str
    example: str | None
    category_id: int
    level: VocabularyLevel


class StudyProgressInput(BaseModel):
    vocabulary_id: int
    result: StudyResult


class StudyProgressResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    vocabulary_id: int
    status: ProgressStatus
    review_count: int
    remembered_count: int
    not_remembered_count: int
    last_reviewed_at: datetime


class StudyProgressSummary(BaseModel):
    total: int
    new: int
    learning: int
    mastered: int


@router.get("/cards", response_model=list[StudyCard])
def get_study_cards(
    category_id: int | None = Query(default=None, ge=1),
    level: VocabularyLevel | None = None,
    limit: int = Query(default=10, ge=1, le=20),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> list[Vocabulary]:
    if limit not in {5, 10, 20}:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="limit must be 5, 10, or 20",
        )

    filters = [Vocabulary.user_id == user.id]
    if category_id is not None:
        filters.append(Vocabulary.category_id == category_id)
    if level is not None:
        filters.append(Vocabulary.level == level)

    return list(
        session.scalars(
            select(Vocabulary)
            .where(*filters)
            .order_by(func.random())
            .limit(limit)
        ).all()
    )


@router.get("/progress", response_model=StudyProgressSummary)
def get_study_progress_summary(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> StudyProgressSummary:
    total = session.scalar(
        select(func.count(Vocabulary.id)).where(Vocabulary.user_id == user.id)
    ) or 0
    status_counts = dict(
        session.execute(
            select(VocabularyProgress.status, func.count(VocabularyProgress.id))
            .where(VocabularyProgress.user_id == user.id)
            .group_by(VocabularyProgress.status)
        ).all()
    )
    learning = status_counts.get("LEARNING", 0)
    mastered = status_counts.get("MASTERED", 0)
    new = total - learning - mastered

    return StudyProgressSummary(
        total=total,
        new=new,
        learning=learning,
        mastered=mastered,
    )


@router.post("/progress", response_model=StudyProgressResponse)
def record_study_progress(
    progress_input: StudyProgressInput,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> VocabularyProgress:
    vocabulary = session.scalar(
        select(Vocabulary).where(
            Vocabulary.id == progress_input.vocabulary_id,
            Vocabulary.user_id == user.id,
        )
    )
    if vocabulary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocabulary not found")

    progress = record_learning_result(
        session,
        user_id=user.id,
        vocabulary_id=vocabulary.id,
        remembered=progress_input.result == "REMEMBERED",
    )
    session.commit()
    session.refresh(progress)
    return progress