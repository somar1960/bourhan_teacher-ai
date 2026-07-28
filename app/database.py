from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
)
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

engine = create_async_engine(
    settings.database_url,
    echo=False,
)

async_session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


# -----------------------------------------
# إنشاء جميع الجداول تلقائياً عند أول تشغيل
# -----------------------------------------
async def create_tables():
    # استيراد جميع الموديلات حتى تُسجل داخل Base.metadata
    from app.models.student import Student
    from app.models.group import Group
    from app.models.exam import Exam
    from app.models.question import Question
    from app.models.option import Option
    from app.models.homework import Homework
    from app.models.homework_submission import HomeworkSubmission
    from app.models.exam_result import ExamResult
    from app.models.student_progress import StudentProgress
    from app.models.file import File
    from app.models.ai_conversation import AIConversation

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)