"""
Question model for Bourhan Teacher AI.
Represents a question within an exam, with a type, points, and optional options.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Enum as SAEnum, Float, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.exam import Exam
    from app.models.option import Option


class QuestionType(str, enum.Enum):
    """Types of questions that can be created."""

    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"


class Question(Base):
    """
    A single question belonging to an exam.
    Supports multiple choice, true/false, and short answer types.
    """

    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    exam_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(
        SAEnum(QuestionType, name="question_type", create_type=True),
        nullable=False,
    )
    points: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    explanation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    exam: Mapped["Exam"] = relationship(
        "Exam", back_populates="questions", lazy="selectin"
    )
    options: Mapped[List["Option"]] = relationship(
        "Option",
        back_populates="question",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Question(id={self.id}, type='{self.question_type}', "
            f"exam_id={self.exam_id})>"
        )