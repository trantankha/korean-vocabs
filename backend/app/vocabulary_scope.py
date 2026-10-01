from sqlalchemy import and_, exists, func, or_, select
from sqlalchemy.orm import aliased
from sqlalchemy.sql.elements import ColumnElement

from app.models import Vocabulary


def visible_vocabulary_condition(user_id: int) -> ColumnElement[bool]:
    personal_vocabulary = aliased(Vocabulary)
    personal_duplicate = exists(
        select(1).where(
            personal_vocabulary.user_id == user_id,
            func.lower(func.trim(personal_vocabulary.word))
            == func.lower(func.trim(Vocabulary.word)),
        )
    )
    return or_(
        Vocabulary.user_id == user_id,
        and_(Vocabulary.user_id.is_(None), ~personal_duplicate),
    )