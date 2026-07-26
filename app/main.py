import asyncio
import threading
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

# ---------- دوال لتشغيل البوتات في خيوط منفصلة ----------
def run_bot_in_thread(bot, bot_name: str):
    """تشغيل بوت في حلقة asyncio منفصلة داخل خيط جديد"""
    def start_bot():
        try:
            # إنشاء حلقة أحداث جديدة لهذا الخيط
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            # تشغيل البوت مع إيقاف إشارات النظام (لتجنب التعارض مع FastAPI)
            loop.run_until_complete(bot.run_polling())
        except Exception as e:
            logger.exception(f"خطأ في تشغيل {bot_name}: {e}")
    
    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()
    logger.info(f"✅ {bot_name} started in background thread")

# ---------- دورة حياة التطبيق ----------
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: تشغيل البوتات في خيوط منفصلة
    if admin_bot:
        run_bot_in_thread(admin_bot, "Admin Bot")
    if student_bot:
        run_bot_in_thread(student_bot, "Student Bot")
    
    yield  # التطبيق يعمل هنا
    
    # Shutdown: لا حاجة لإيقاف البوتات لأنها تشغل في خيوط daemon
    logger.info("🛑 Application shutting down...")

# ---------- إنشاء تطبيق FastAPI ----------
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
