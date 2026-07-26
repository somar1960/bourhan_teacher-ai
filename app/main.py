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

# ---------- دوال تشغيل البوتات في خيوط منفصلة مع تنظيف ----------
def run_bot_in_thread(bot, bot_name: str):
    """تشغيل البوت في خيط منفصل مع حلقة أحداث مستقلة"""
    def start_bot():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # ⭐ تنظيف الـ webhook لتجنب Conflict
            async def cleanup_and_run():
                try:
                    # حذف الـ webhook القديم وإسقاط التحديثات المعلقة
                    await bot.bot.delete_webhook(drop_pending_updates=True)
                    # مهلة صغيرة لتتلاشى الجلسات القديمة
                    await asyncio.sleep(0.5)
                    # تشغيل Polling
                    await bot.run_polling(stop_signals=None)
                except Exception as e:
                    logger.exception(f"❌ خطأ أثناء تشغيل {bot_name}: {e}")
            
            loop.run_until_complete(cleanup_and_run())
        except Exception as e:
            logger.exception(f"❌ {bot_name} error: {e}")
        finally:
            loop.close()
    
    thread = threading.Thread(target=start_bot, daemon=True)
    thread.start()
    logger.info(f"🚀 {bot_name} started in background thread")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # بدء البوتات
    if admin_bot:
        run_bot_in_thread(admin_bot, "Admin Bot")
    if student_bot:
        run_bot_in_thread(student_bot, "Student Bot")
    
    yield  # التطبيق يعمل هنا
    
    # عند الإغلاق، الخيوط daemon ستنتهي تلقائياً
    logger.info("🛑 Application shutting down...")

# ---------- تطبيق FastAPI ----------
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
