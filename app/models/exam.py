"""
Exam model for Bourhan Teacher AI.
Represents an exam assigned to a group, with questions and results.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.exam_result import ExamResult
    from app.models.group import Group
    from app.models.question import Question


class Exam(Base):
    """
    Represents an exam assigned to a teaching group.

    Each exam belongs to one group, contains multiple questions,
    and stores multiple student results.
    """

    __tablename__ = "exams"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    group_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    duration_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
    )

    total_marks: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=100.0,
    )

    start_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    end_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default="true",
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # =========================
    # Relationships
    # =========================

    group: Mapped["Group"] = relationship(
        "Group",
        back_populates="exams",
        lazy="selectin",
    )

    questions: Mapped[List["Question"]] = relationship(
        "Question",
        back_populates="exam",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    results: Mapped[List["ExamResult"]] = relationship(
        "ExamResult",
        back_populates="exam",
        lazy="selectin",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return (
            f"<Exam(id={self.id}, "
            f"title='{self.title}', "
            f"group_id={self.group_id})>"
        )