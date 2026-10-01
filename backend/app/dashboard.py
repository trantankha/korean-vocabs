from typing import Literal

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.auth import get_current_user
from app.database import get_db
from app.models import Category, User, Vocabulary
from app.vocabulary_scope import visible_vocabulary_condition

router = APIRouter(prefix="/dashboard", tags=["dashboard"])
VocabularyLevel = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]
LEVELS: tuple[VocabularyLevel, ...] = ("BEGINNER", "INTERMEDIATE", "ADVANCED")


class LevelCount(BaseModel):
    level: VocabularyLevel
    count: int


class CategoryCount(BaseModel):
    id: int
    slug: str
    name_ko: str
    name_en: str
    count: int


class DashboardStats(BaseModel):
    total_vocabulary: int
    by_level: list[LevelCount]
    categories_used: int
    by_category: list[CategoryCount]


@router.get("/stats", response_model=DashboardStats)
def read_dashboard_stats(
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> DashboardStats:
    level_counts = dict(
        session.execute(
            select(Vocabulary.level, func.count(Vocabulary.id))
            .where(visible_vocabulary_condition(user.id))
            .group_by(Vocabulary.level)
        ).all()
    )
    category_rows = session.execute(
        select(
            Category.id,
            Category.slug,
            Category.name_ko,
            Category.name_en,
            func.count(Vocabulary.id),
        )
        .join(Vocabulary, Vocabulary.category_id == Category.id)
        .where(visible_vocabulary_condition(user.id))
        .group_by(Category.id, Category.slug, Category.name_ko, Category.name_en)
        .order_by(Category.id)
    ).all()

    by_level = [LevelCount(level=level, count=level_counts.get(level, 0)) for level in LEVELS]
    by_category = [
        CategoryCount(
            id=category_id,
            slug=slug,
            name_ko=name_ko,
            name_en=name_en,
            count=count,
        )
        for category_id, slug, name_ko, name_en, count in category_rows
    ]

    return DashboardStats(
        total_vocabulary=sum(level.count for level in by_level),
        by_level=by_level,
        categories_used=len(by_category),
        by_category=by_category,
    )