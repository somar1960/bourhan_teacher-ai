"""
ExamResult model for Bourhan Teacher AI.
Records a student's attempt and score for a specific exam.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.exam import Exam
    from app.models.student import Student


class ExamResult(Base):
    """
    Represents the result of a student's exam attempt.
    """

    __tablename__ = "exam_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exam_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("exams.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    max_score: Mapped[float] = mapped_column(Float, nullable=False, default=100.0)
    percentage: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    passed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    finished_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
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
    student: Mapped["Student"] = relationship(
        "Student", back_populates="results", lazy="selectin"
    )
    exam: Mapped["Exam"] = relationship(
        "Exam", back_populates="results", lazy="selectin"
    )

    def __repr__(self) -> str:
        return (
            f"<ExamResult(id={self.id}, student_id={self.student_id}, "
            f"exam_id={self.exam_id}, score={self.score}/{self.max_score})>"
        )