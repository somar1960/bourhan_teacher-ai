from sqlalchemy import String, ForeignKey, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Option(Base):
    __tablename__ = "options"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id"),
        nullable=False
    )

    text: Mapped[str] = mapped_column(
        String(500),
        nullable=False
    )

    is_correct: Mapped[bool] = mapped_column(
        Boolean,
        default=False
    )

    question = relationship(
        "Question",
        back_populates="options"
    )
