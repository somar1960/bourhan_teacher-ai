import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager
from sqlalchemy import text

from app.config import settings
from app.database import async_session

try:
    from app.bots.admin_bot.main import admin_bot
    from app.bots.student_bot.main import student_bot
except Exception as e:
    logging.exception("خطأ في تحميل البوتات")
    admin_bot = None
    student_bot = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# متغير لتخزين مهام البوتات
bot_tasks = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """تشغيل البوتات باستخدام Polling في نفس حلقة الأحداث"""
    # بدء تشغيل البوتات كمهام خلفية
    if admin_bot:
        task = asyncio.create_task(admin_bot.run_polling())
        bot_tasks.append(task)
        logger.info("✅ Admin Bot started (Polling)")
    
    if student_bot:
        task = asyncio.create_task(student_bot.run_polling())
        bot_tasks.append(task)
        logger.info("✅ Student Bot started (Polling)")
    
    yield  # التطبيق يعمل هنا
    
    # إيقاف البوتات بشكل آمن
    logger.info("🛑 Shutting down bots...")
    for task in bot_tasks:
        task.cancel()
    await asyncio.gather(*bot_tasks, return_exceptions=True)
    logger.info("✅ Bots stopped")

# إنشاء تطبيق FastAPI (فقط لـ Health Check)
app = FastAPI(
    title="Bourhan Teacher AI",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/")
async def root():
    return {
        "project": "Bourhan Teacher AI",
        "message": "Platform is running 🚀",
        "environment": settings.environment,
        "bots": {
            "admin": "active" if admin_bot else "inactive",
            "student": "active" if student_bot else "inactive"
        }
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/db")
async def health_db():
    try:
        async with async_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "db_ok"}
    except Exception as e:
        logger.exception("Database health check failed")
        return {"status": "db_error", "detail": str(e)}