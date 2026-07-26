import logging
from openai import AsyncOpenAI

from app.config import settings
from app.database import async_session
from app.models.student import Student, StudentTrack, StudentLevel

logger = logging.getLogger(__name__)

if not settings.openai_api_key:
    logger.warning("⚠️ OPENAI_API_KEY غير موجود.")
    client = None
else:
    client = AsyncOpenAI(api_key=settings.openai_api_key)

async def get_ai_response(student_id: int, question: str) -> str:
    if not client:
        return "❌ الذكاء الاصطناعي غير مفعل."

    async with async_session() as session:
        student = await session.get(Student, student_id)
        if not student:
            return "⚠️ الطالب غير موجود."

        # ✅ التعامل مع الـ Enum
        track = student.track or StudentTrack.CONVERSATION
        level = student.level.value if student.level else "Unknown"

        # تحديد التعليمات
        if track == StudentTrack.SCIENTIFIC:
            base_instruction = "أنت معلم إنجليزي متخصص في المواد العلمية (فيزياء، كيمياء، رياضيات)."
            track_display = "العلمي"
        elif track == StudentTrack.LITERARY:
            base_instruction = "أنت معلم إنجليزي متخصص في المواد الأدبية (القواعد، البلاغة، الأدب)."
            track_display = "الأدبي"
        else:
            base_instruction = "أنت معلم محادثة إنجليزية. ركز على المحادثات اليومية."
            track_display = "المحادثات العامة"

        prompt = f"""
{base_instruction}

معلومات عن الطالب:
- المسار: {track_display}
- المستوى: {level}

سؤال الطالب: {question}

تعليمات:
1. اشرح بالعربية بطريقة بسي
