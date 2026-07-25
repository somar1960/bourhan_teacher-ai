import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import settings

# استيراد البوتات
try:
    from app.bots.student_bot.main import student_bot
except Exception as e:
    logging.error(f"خطأ في تحميل البوت: {e}")
    student_bot = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """تشغيل البوتات عند بدء التطبيق"""
    if student_bot:
        logger.info("🚀 تشغيل بوت الطالب...")
        asyncio.create_task(student_bot.run_polling())
    yield
    # هنا نضع أي تنظيف عند الإغلاق (اختياري)

app = FastAPI(
    title="Bourhan Teacher AI",
    description="منصة تعليمية ذكية للمعلم والطالب",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "project": "Bourhan Teacher AI",
        "message": "Platform is running 🚀",
        "environment": settings.environment,
        "timezone": settings.timezone,
        "bots": {
            "student": "active" if student_bot else "inactive"
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok", "service": "Bourhan Teacher AI"}
