"""
Homework model for Bourhan Teacher AI.
Defines the homework table and its relationship with groups.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.group import Group
    from app.models.homework_submission import HomeworkSubmission


class HomeworkStatus(str, enum.Enum):
    """Status of a homework assignment."""

    PENDING = "pending"
    SUBMITTED = "submitted"
    GRADED = "graded"
    ARCHIVED = "archived"


class Homework(Base):
    """
    Represents a homework assignment assigned to a specific group.
    """

    __tablename__ = "homeworks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    due_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    group_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[HomeworkStatus] = mapped_column(
        SAEnum(HomeworkStatus, name="homework_status", create_type=True),
        nullable=False,
        default=HomeworkStatus.PENDING,
        server_default="pending",   # ✅ التعديل الأول
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

    # علاقة مع المجموعة
    group: Mapped["Group"] = relationship(
        "Group",
        back_populates="homeworks",
        lazy="selectin",
    )

    # ✅ التعديل الثاني: علاقة مع تسليمات الطلاب
    submissions: Mapped[list["HomeworkSubmission"]] = relationship(
        "HomeworkSubmission",
        back_populates="homework",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return (
            f"<Homework(id={self.id}, "
            f"title='{self.title}', "
            f"status='{self.status.value}')>"
        )