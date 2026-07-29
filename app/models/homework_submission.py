"""
HomeworkSubmission model for Bourhan Teacher AI.
Defines the submissions table, linking students to their submitted homework.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
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
    from app.models.homework import Homework
    from app.models.student import Student


class HomeworkSubmissionStatus(str, enum.Enum):
    """Status of a homework submission."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    REVIEWED = "reviewed"


class HomeworkSubmission(Base):
    """
    Represents a student's submission for a specific homework assignment.
    """

    __tablename__ = "homework_submissions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    homework_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("homeworks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    submission_text: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    file_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
    )

    grade: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    teacher_note: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[HomeworkSubmissionStatus] = mapped_column(
        SAEnum(
            HomeworkSubmissionStatus,
            name="submission_status",
            create_type=True,
        ),
        nullable=False,
        default=HomeworkSubmissionStatus.PENDING,
        server_default="pending",
    )

    submitted_at: Mapped[datetime] = mapped_column(
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

    # Relationships

    homework: Mapped["Homework"] = relationship(
        "Homework",
        back_populates="submissions",
        lazy="selectin",
    )

    student: Mapped["Student"] = relationship(
        "Student",
        back_populates="submissions",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<HomeworkSubmission("
            f"id={self.id}, "
            f"homework_id={self.homework_id}, "
            f"student_id={self.student_id}, "
            f"status='{self.status.value}')>"
        )