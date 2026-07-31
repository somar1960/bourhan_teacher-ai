"""
Student model for Bourhan Teacher AI.
Defines the students table, their attributes, and relationships.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional, List

from sqlalchemy import BigInteger, Boolean, DateTime, Enum as SAEnum, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.exam_result import ExamResult
    from app.models.homework_submission import HomeworkSubmission


class StudentTrack(str, enum.Enum):
    """Academic track of the student."""

    SCIENTIFIC = "scientific"
    LITERARY = "literary"
    CONVERSATION = "conversation"


class StudentLevel(str, enum.Enum):
    """Proficiency level of the student."""

    UNKNOWN = "unknown"
    A1 = "a1"
    A2 = "a2"
    B1 = "b1"
    B2 = "b2"
    C1 = "c1"
    C2 = "c2"


class Student(Base):
    """
    Represents a student enrolled in the Bourhan Teacher AI system.

    Each student belongs to an optional group and has a specific academic
    track and proficiency level.
    """

    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(
        String(20), unique=True, nullable=False
    )
    telegram_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, unique=True, nullable=True, index=True
    )
    group_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True
    )
    track: Mapped[StudentTrack] = mapped_column(
        SAEnum(StudentTrack, name="student_track", create_type=True),
        nullable=False,
    )
    level: Mapped[StudentLevel] = mapped_column(
        SAEnum(StudentLevel, name="student_level", create_type=True),
        nullable=False,
        default=StudentLevel.UNKNOWN,
    )
    is_approved: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    weak_topics: Mapped[list[str]] = mapped_column(
        JSONB, nullable=False, default=lambda: []
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
    group: Mapped[Optional["Group"]] = relationship(
        "Group", back_populates="students", lazy="selectin"
    )
    results: Mapped[List["ExamResult"]] = relationship(
        "ExamResult", back_populates="student", lazy="selectin"
    )
    submissions: Mapped[List["HomeworkSubmission"]] = relationship(
        "HomeworkSubmission", back_populates="student", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, name='{self.name}')>"