from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.database import Base

class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, unique=True, nullable=False)
    telegram_id = Column(String, nullable=True, unique=True)
    
    # هذا هو الحقل الجديد لتحديد المسار
    track = Column(String, nullable=True)  # قيم محتملة: scientific, literary, conversation
    
    level = Column(String, default="مبتدئ")  # مستوى الطالب
    weak_topics = Column(String, nullable=True)  # نقاط الضعف
    
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())

    # العلاقات مع الجداول الأخرى (مثل المجموعات، الامتحانات) موجودة مسبقاً
