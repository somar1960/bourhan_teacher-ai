import logging
from openai import AsyncOpenAI

from app.config import settings
from app.database import async_session
from app.models.student import Student, StudentTrack, StudentLevel

logger = logging.getLogger(__name__)

if not settings.openai_api_key:
    logger.warning("⚠️ OPENAI_API_KEY غير موجود في الإعدادات.")
    client = None
else:
    client = AsyncOpenAI(api_key=settings.openai_api_key)

async def get_ai_response(student_id: int, question: str) -> str:
    if not client:
        return "❌ الذكاء الاصطناعي غير مفعل. يرجى إضافة مفتاح OPENAI_API_KEY في الإعدادات."

    async with async_session() as session:
        student = await session.get(Student, student_id)
        if not student:
            return "⚠️ الطالب غير موجود."

        # ✅ التعامل مع الـ Enum
        track = student.track or StudentTrack.CONVERSATION
        level = student.level.value if student.level else "Unknown"

        # بناء التعليمات حسب المسار
        if track == StudentTrack.SCIENTIFIC:
            base_instruction = "أنت معلم لغة إنجليزية متخصص في المواد العلمية (فيزياء، كيمياء، رياضيات)."
            track_display = "العلمي"
        elif track == StudentTrack.LITERARY:
            base_instruction = "أنت معلم لغة إنجليزية متخصص في المواد الأدبية (القواعد، البلاغة، الأدب)."
            track_display = "الأدبي"
        else:
            base_instruction = "أنت معلم محادثة إنجليزية. ركز على المحادثات اليومية والسفر."
            track_display = "المحادثات العامة"

        # ✅ تم إصلاح الخطأ هنا: إضافة الإغلاق الصحيح للثلاث علامات تنصيص
        prompt = f"""
{base_instruction}

معلومات عن الطالب:
- المسار: {track_display}
- المستوى: {level}

سؤال الطالب: {question}

تعليمات:
1. اشرح بالعربية بطريقة بسيطة جداً (مناسبة للمستوى).
2. أعط 2-3 أمثلة باللغة الإنجليزية مع ترجمتها.
3. اختبر فهم الطالب بطرح سؤال تفاعلي في النهاية.
4. **لا تعطِ الحل النهائي مباشرة**. إذا كان السؤال تمريناً، اشرح الخطوات وساعده حتى يصل للحل بنفسه.
5. كن مشجعاً ودوداً.

الرد:
"""  # <- هذا هو الإغلاق الذي كان مفقوداً

        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1200
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.exception(f"خطأ في مكالمة OpenAI: {e}")
            return f"❌ عذراً، حدث خطأ تقني: {str(e)}"
