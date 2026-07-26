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
    # بدء تشغيل البوتات كـ Tasks داخل نفس Event Loop
    if admin_bot:
        task = asyncio.create_task(run_bot_polling(admin_bot, "Admin Bot"))
        bot_tasks.append(task)
    if student_bot:
        task = asyncio.create_task(run_bot_polling(student_bot, "Student Bot"))
        bot_tasks.append(task)

    yield  # هنا يعمل التطبيق

    # إيقاف البوتات بشكل آمن
    logger.info("🛑 Shutting down bots...")
    for task in bot_tasks:
        task.cancel()
    await asyncio.gather(*bot_tasks, return_exceptions=True)
    logger.info("✅ Bots stopped")

async def run_bot_polling(bot, bot_name: str):
    """تشغيل البوت مع منع معالجة الإشارات"""
    try:
        logger.info(f"🚀 Starting {bot_name}...")
        # منع محاولة إضافة Signal Handlers في الخيط الرئيسي
        await bot.run_polling(stop_signals=None)
    except asyncio.CancelledError:
        logger.info(f"⏹️ {bot_name} stopped gracefully")
    except Exception as e:
        logger.exception(f"❌ {bot_name} error: {e}")

# إنشاء تطبيق FastAPI
app = FastAPI(
    title="Bourhan Teacher AI",
    description="AI Educational Platform for Teachers and Students",
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
