"""
Group model for Bourhan Teacher AI.
Defines the groups table and its relationships.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum as SAEnum,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.student import StudentTrack

if TYPE_CHECKING:
    from app.models.student import Student
    from app.models.file import File
    from app.models.homework import Homework


class Group(Base):
    """
    Represents a teaching group in Bourhan Teacher AI.
    """

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        default="",
    )

    track: Mapped[StudentTrack] = mapped_column(
        SAEnum(StudentTrack, name="group_track", create_type=True),
        nullable=False,
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

    # ================= Relationships =================

    students: Mapped[list["Student"]] = relationship(
        "Student",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    files: Mapped[list["File"]] = relationship(
        "File",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    homeworks: Mapped[list["Homework"]] = relationship(
        "Homework",
        back_populates="group",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    def __repr__(self) -> str:
        return f"<Group(id={self.id}, name='{self.name}')>"