import os
import logging
from openai import AsyncOpenAI
from sqlalchemy import select

from app.database import async_session
from app.models.student import Student

logger = logging.getLogger(__name__)

# التحقق من وجود المفتاح
API_KEY = os.getenv("OPENAI_API_KEY")
if not API_KEY:
    logger.warning("⚠️ OPENAI_API_KEY غير موجود. الذكاء الاصطناعي لن يعمل حتى تضيفه في Railway.")
    client = None
else:
    client = AsyncOpenAI(api_key=API_KEY)

async def get_ai_response(student_id: int, question: str) -> str:
    """ترجع رد الذكاء الاصطناعي حسب مستوى ومسار الطالب"""
    
    if not client:
        return "❌ الذكاء الاصطناعي غير مفعل. يرجى إضافة مفتاح OPENAI_API_KEY في الإعدادات."
    
    async with async_session() as session:
        student = await session.get(Student, student_id)
        if not student:
            return "⚠️ الطالب غير موجود."

        # تحديد نمط الرد حسب المسار
        track = student.track or "conversation"
        level = student.level or "مبتدئ"
        weak_topics = student.weak_topics or "لا يوجد"

        # بناء التعليمات الأساسية حسب المسار
        if track == "scientific":
            base_instruction = "أنت معلم لغة إنجليزية متخصص في المواد العلمية (فيزياء، كيمياء، أحياء، رياضيات). ركز على المصطلحات العلمية وترجمتها."
        elif track == "literary":
            base_instruction = "أنت معلم لغة إنجليزية متخصص في المواد الأدبية. ركز على القواعد النحوية، البلاغة، الأدب، وتحليل النصوص."
        else:  # conversation
            base_instruction = "أنت معلم محادثة إنجليزية. ركز على المحادثات اليومية، السفر، المطاعم، التسوق، النطق الصحيح، والتعبيرات الشائعة."

        # بناء البرومبت النهائي
        prompt = f"""
{base_instruction}

معلومات عن الطالب:
- المستوى: {level}
- نقاط الضعف: {weak_topics}

سؤال الطالب: {question}

تعليمات عامة:
1. اشرح القاعدة أو المعلومة بالعربية بطريقة بسيطة جداً (مناسبة للمستوى).
2. أعط 2-3 أمثلة باللغة الإنجليزية مع ترجمتها.
3. اختبر فهم الطالب بطرح سؤال تفاعلي في النهاية.
4. **لا تعطِ الحل النهائي مباشرة**. إذا كان السؤال تمريناً، اشرح الخطوات وساعده حتى يصل للحل بنفسه.
5. كن مشجعاً ودوداً.

الرد:
"""
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",  # أو gpt-3.5-turbo إذا أردت توفير التكاليف
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1200
            )
            answer = response.choices[0].message.content
            return answer
        except Exception as e:
            logger.error(f"خطأ في مكالمة OpenAI: {e}")
            return f"❌ عذراً، حدث خطأ تقني: {str(e)}"
