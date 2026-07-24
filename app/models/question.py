from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    exam_id: Mapped[int] = mapped_column(
        ForeignKey("exams.id"),
        nullable=False
    )

    question_text: Mapped[str] = mapped_column(
        String(1000),
        nullable=False
    )

    correct_answer: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    exam = relationship(
        "Exam",
        back_populates="questions"
    )

    options = relationship(
        "Option",
        back_populates="question"
    )
