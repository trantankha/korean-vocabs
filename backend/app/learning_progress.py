from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import VocabularyProgress

MASTERY_THRESHOLD = 3


def record_learning_result(
    session: Session,
    user_id: int,
    vocabulary_id: int,
    remembered: bool,
) -> VocabularyProgress:
    progress = session.scalar(
        select(VocabularyProgress).where(
            VocabularyProgress.user_id == user_id,
            VocabularyProgress.vocabulary_id == vocabulary_id,
        )
    )
    if progress is None:
        progress = VocabularyProgress(
            user_id=user_id,
            vocabulary_id=vocabulary_id,
            review_count=0,
            remembered_count=0,
            not_remembered_count=0,
        )
        session.add(progress)

    progress.review_count += 1
    progress.last_reviewed_at = func.now()
    if remembered:
        progress.remembered_count += 1
    else:
        progress.not_remembered_count += 1

    progress.status = (
        "MASTERED"
        if progress.remembered_count >= MASTERY_THRESHOLD
        else "LEARNING"
    )
    return progress