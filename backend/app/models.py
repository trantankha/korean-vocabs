from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    vocabularies: Mapped[list["Vocabulary"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    slug: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name_ko: Mapped[str] = mapped_column(String(100), nullable=False)
    name_en: Mapped[str] = mapped_column(String(100), nullable=False)

    vocabularies: Mapped[list["Vocabulary"]] = relationship(back_populates="category")


class Vocabulary(Base):
    __tablename__ = "vocabularies"
    __table_args__ = (
        CheckConstraint(
            "level IN ('BEGINNER', 'INTERMEDIATE', 'ADVANCED')",
            name="ck_vocabularies_level",
        ),
        Index("ix_vocabularies_user_created_at", "user_id", "created_at"),
        Index("ix_vocabularies_user_category", "user_id", "category_id"),
        Index("ix_vocabularies_user_level", "user_id", "level"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    word: Mapped[str] = mapped_column(String(200), nullable=False)
    meaning: Mapped[str] = mapped_column(Text, nullable=False)
    example: Mapped[str | None] = mapped_column(Text)
    example_en: Mapped[str | None] = mapped_column(Text)
    category_id: Mapped[int] = mapped_column(
        ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )
    level: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User | None] = relationship(back_populates="vocabularies")
    category: Mapped[Category] = relationship(back_populates="vocabularies")


class VocabularyProgress(Base):
    __tablename__ = "vocabulary_progress"
    __table_args__ = (
        CheckConstraint(
            "status IN ('NEW', 'LEARNING', 'MASTERED')",
            name="ck_vocabulary_progress_status",
        ),
        CheckConstraint(
            "review_count >= 0 AND remembered_count >= 0 AND not_remembered_count >= 0",
            name="ck_vocabulary_progress_counts_nonnegative",
        ),
        UniqueConstraint("user_id", "vocabulary_id", name="uq_vocabulary_progress_user_vocabulary"),
        Index("ix_vocabulary_progress_user_status", "user_id", "status"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    vocabulary_id: Mapped[int] = mapped_column(
        ForeignKey("vocabularies.id", ondelete="CASCADE"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="NEW")
    review_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    remembered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    not_remembered_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class QuizAnswerReceipt(Base):
    __tablename__ = "quiz_answer_receipts"
    __table_args__ = (Index("ix_quiz_answer_receipts_created_at", "created_at"),)

    token_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    vocabulary_id: Mapped[int] = mapped_column(
        ForeignKey("vocabularies.id", ondelete="CASCADE"), nullable=False
    )
    selected_choice_id: Mapped[str] = mapped_column(String(32), nullable=False)
    correct: Mapped[bool] = mapped_column(Boolean, nullable=False)
    selected_answer: Mapped[str] = mapped_column(Text, nullable=False)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    example: Mapped[str | None] = mapped_column(Text)
    example_en: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())