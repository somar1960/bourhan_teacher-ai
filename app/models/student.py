from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

# --- Enums ---
class StudentTrack(str, enum.Enum):
    SCIENTIFIC = "scientific"
    LITERARY = "literary"
    CONVERSATION = "conversation"

class StudentLevel(str, enum.Enum):
    UNKNOWN = "Unknown"
    A1 = "A1"
    A2 = "A2"
    B1 = "B1"
    B2 = "B2"
    C1 = "C1"
    C2 = "C2"

# --- النموذج الرئيسي ---
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    telegram_id = Column(String(20), nullable=True, unique=True)

    # ✅ إضافة المفتاح الخارجي للمجموعة
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    track = Column(SQLEnum(StudentTrack), nullable=True)
    level = Column(SQLEnum(StudentLevel), default=StudentLevel.UNKNOWN)

    # TODO: سيتم نقل weak_topics إلى جدول مستقل لاحقاً
    weak_topics = Column(String, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    # ✅ العلاقة مع المجموعة
    group = relationship("Group", back_populates="students")
