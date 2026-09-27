from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Path, Query, Response, status
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.auth import get_current_user
from app.database import get_db
from app.models import Category, User, Vocabulary

router = APIRouter(tags=["vocabulary"])
VocabularyLevel = Literal["BEGINNER", "INTERMEDIATE", "ADVANCED"]
VocabularySort = Literal["created_at_desc", "created_at_asc"]


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    name_ko: str
    name_en: str


class VocabularyInput(BaseModel):
    word: str = Field(max_length=200)
    meaning: str = Field(max_length=10000)
    example: str | None = Field(default=None, max_length=10000)
    category_id: int = Field(gt=0)
    level: VocabularyLevel

    @field_validator("word", "meaning")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("This field cannot be empty")
        return value

    @field_validator("example")
    @classmethod
    def strip_optional_example(cls, value: str | None) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None


class VocabularyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    word: str
    meaning: str
    example: str | None
    category_id: int
    category: CategoryResponse
    level: VocabularyLevel
    created_at: datetime
    updated_at: datetime


class VocabularyPage(BaseModel):
    items: list[VocabularyResponse]
    page: int
    limit: int
    total: int
    total_pages: int


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(session: Session = Depends(get_db)) -> list[Category]:
    return list(session.scalars(select(Category).order_by(Category.id)))


@router.get("/vocabularies", response_model=VocabularyPage)
def list_vocabularies(
    search: str | None = Query(default=None, max_length=200),
    category_id: int | None = Query(default=None, ge=1),
    level: VocabularyLevel | None = None,
    sort: VocabularySort = "created_at_desc",
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> VocabularyPage:
    filters = [Vocabulary.user_id == user.id]
    normalized_search = search.strip() if search else ""
    if normalized_search:
        search_pattern = f"%{normalized_search}%"
        filters.append(
            or_(Vocabulary.word.ilike(search_pattern), Vocabulary.meaning.ilike(search_pattern))
        )
    if category_id is not None:
        filters.append(Vocabulary.category_id == category_id)
    if level is not None:
        filters.append(Vocabulary.level == level)

    total = session.scalar(select(func.count()).select_from(Vocabulary).where(*filters)) or 0
    ordering = (
        (Vocabulary.created_at.asc(), Vocabulary.id.asc())
        if sort == "created_at_asc"
        else (Vocabulary.created_at.desc(), Vocabulary.id.desc())
    )
    items = session.scalars(
        select(Vocabulary)
        .options(selectinload(Vocabulary.category))
        .where(*filters)
        .order_by(*ordering)
        .offset((page - 1) * limit)
        .limit(limit)
    ).all()

    return VocabularyPage(
        items=list(items),
        page=page,
        limit=limit,
        total=total,
        total_pages=(total + limit - 1) // limit,
    )


def get_owned_vocabulary(session: Session, user_id: int, vocabulary_id: int) -> Vocabulary:
    vocabulary = session.scalar(
        select(Vocabulary)
        .options(selectinload(Vocabulary.category))
        .where(Vocabulary.id == vocabulary_id, Vocabulary.user_id == user_id)
    )
    if vocabulary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vocabulary not found")
    return vocabulary


def ensure_category_exists(session: Session, category_id: int) -> None:
    if session.get(Category, category_id) is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Invalid category_id")


@router.post(
    "/vocabularies",
    response_model=VocabularyResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_vocabulary(
    vocabulary_input: VocabularyInput,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Vocabulary:
    ensure_category_exists(session, vocabulary_input.category_id)
    vocabulary = Vocabulary(user_id=user.id, **vocabulary_input.model_dump())
    session.add(vocabulary)
    session.commit()
    session.refresh(vocabulary)
    return get_owned_vocabulary(session, user.id, vocabulary.id)


@router.get("/vocabularies/{vocabulary_id}", response_model=VocabularyResponse)
def read_vocabulary(
    vocabulary_id: int = Path(ge=1),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Vocabulary:
    return get_owned_vocabulary(session, user.id, vocabulary_id)


@router.put("/vocabularies/{vocabulary_id}", response_model=VocabularyResponse)
def update_vocabulary(
    vocabulary_input: VocabularyInput,
    vocabulary_id: int = Path(ge=1),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Vocabulary:
    vocabulary = get_owned_vocabulary(session, user.id, vocabulary_id)
    ensure_category_exists(session, vocabulary_input.category_id)
    for field, value in vocabulary_input.model_dump().items():
        setattr(vocabulary, field, value)
    session.commit()
    session.refresh(vocabulary)
    return get_owned_vocabulary(session, user.id, vocabulary.id)


@router.delete("/vocabularies/{vocabulary_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vocabulary(
    vocabulary_id: int = Path(ge=1),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_db),
) -> Response:
    vocabulary = get_owned_vocabulary(session, user.id, vocabulary_id)
    session.delete(vocabulary)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)