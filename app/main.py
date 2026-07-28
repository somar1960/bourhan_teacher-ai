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

# ---------- دالة تشغيل البوت في خيط منفصل ----------
async def run_bot_in_thread(bot, bot_name: str):
    """تشغيل البوت في خيط منفصل مع حلقة أحداث مستقلة"""
    def start_bot():
        try:
            # إنشاء حلقة أحداث جديدة لهذا الخيط
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # ✅ حذف أي ويب هوك معلق بشكل صحيح (من خلال bot.bot)
            loop.run_until_complete(bot.bot.delete_webhook(drop_pending_updates=True))
            
            # تشغيل البوت مع تعطيل إشارات النظام
            loop.run_until_complete(bot.run_polling(stop_signals=None))
        except Exception as e:
            logger.exception(f"❌ {bot_name} error: {e}")
        finally:
            loop.close()
    
    # تشغيل الدالة في خيط منفصل
    await asyncio.to_thread(start_bot)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """تشغيل البوتات في خيوط منفصلة"""
    tasks = []
    if admin_bot:
        task = asyncio.create_task(run_bot_in_thread(admin_bot, "Admin Bot"))
        tasks.append(task)
        logger.info("🚀 Admin Bot started in background thread")
    
    if student_bot:
        task = asyncio.create_task(run_bot_in_thread(student_bot, "Student Bot"))
        tasks.append(task)
        logger.info("🚀 Student Bot started in background thread")
    
    yield  # التطبيق يعمل هنا
    
    # إلغاء المهام (البوتات ستتوقف تلقائياً عند إغلاق الخيوط)
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    logger.info("🛑 Bots stopped")

# إنشاء تطبيق FastAPI
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