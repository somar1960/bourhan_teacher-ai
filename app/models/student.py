from sqlalchemy import String, BigInteger, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    telegram_id: Mapped[int] = mapped_column(
        BigInteger,
        unique=True,
        nullable=False
    )

    full_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False
    )

    phone_number: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True
    )

    password_hash: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True
    )

    language: Mapped[str] = mapped_column(
        String(10),
        default="ar"
    )

    level: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True
    )

    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow
    )

    group = relationship(
        "Group",
        back_populates="students"
    )
