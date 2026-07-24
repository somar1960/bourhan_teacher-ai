from sqlalchemy import ForeignKey, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from app.database import Base


class ExamResult(Base):
    __tablename__ = "exam_results"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id"),
        nullable=False
    )

    student_id: Mapped[int] = mapped_column(
        ForeignKey("students.id"),
        nullable=False
    )

    score: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    correct_answers: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    wrong_answers: Mapped[int] = mapped_column(
        Integer,
        default=0
    )

    completed_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )
