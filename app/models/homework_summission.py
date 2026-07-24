from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base


class HomeworkSubmission(Base):
    __tablename__ = "homework_submissions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    homework_id: Mapped[int] = mapped_column(
        ForeignKey("homeworks.id"),
        nullable=False
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False
    )

    answer_text: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True
    )

    file_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True
    )

    score: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True
    )

    status: Mapped[str] = mapped_column(
        String(50),
        default="pending"
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )


    homework = relationship(
        "Homework"
    )

    student = relationship(
        "Student"
    )
