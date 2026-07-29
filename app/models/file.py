"""
File model for Bourhan Teacher AI.
Defines the files table for uploaded materials (PDF, DOCX, images, video, audio)
linked to groups.
"""

from __future__ import annotations

import enum
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.group import Group

class FileType(str, enum.Enum):
    """Supported file types for educational materials."""

    PDF = "pdf"
    DOCX = "docx"
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"

class File(Base):
    """
    Represents an uploaded file (resource) belonging to an optional group.
    """

    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    file_type: Mapped[FileType] = mapped_column(
        SAEnum(FileType, name="file_type", create_type=True),
        nullable=False,
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_size: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    uploaded_by: Mapped[Optional[int]] = mapped_column(
        BigInteger, nullable=True, comment="Telegram user ID of the uploader"
    )
    group_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True, index=True
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

    # Relationship to Group (requires "files" relationship in Group model)
    group: Mapped[Optional["Group"]] = relationship(
        "Group", back_populates="files", lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<File(id={self.id}, title='{self.title}', type='{self.file_type}')>"