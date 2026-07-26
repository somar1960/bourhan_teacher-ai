from sqlalchemy import String, Boolean, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base

class Group(Base):
    __tablename__ = "groups"  # ✅ تم التصحيح (كانت _tablename__)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # ✅ العلاقة مع الطلاب (تم التصحيح)
    students: Mapped[list["Student"]] = relationship(
        "Student",
        back_populates="group",
        lazy="selectin"
    )
