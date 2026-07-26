import asyncio
import logging
from fastapi import FastAPI, Request, Response
from contextlib import asynccontextmanager
from sqlalchemy import text
from telegram import Update
from telegram.ext import ContextTypes, Application

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

# متغيرات للتحكم
ADMIN_WEBHOOK_URL = f"{settings.WEBHOOK_BASE_URL}/webhook/admin"
STUDENT_WEBHOOK_URL = f"{settings.WEBHOOK_BASE_URL}/webhook/student"

@asynccontextmanager
async def lifespan(app: FastAPI):
    # بدء التشغيل: تهيئة البوتات وتعيين Webhooks
    if admin_bot:
        await admin_bot.initialize()
        await admin_bot.bot.set_webhook(
            url=ADMIN_WEBHOOK_URL,
            drop_pending_updates=True
        )
        logger.info(f"✅ Admin Webhook set to {ADMIN_WEBHOOK_URL}")

    if student_bot:
        await student_bot.initialize()
        await student_bot.bot.set_webhook(
            url=STUDENT_WEBHOOK_URL,
            drop_pending_updates=True
        )
        logger.info(f"✅ Student Webhook set to {STUDENT_WEBHOOK_URL}")

    yield  # التطبيق يعمل هنا

    # الإغلاق: حذف Webhooks وإيقاف البوتات
    if admin_bot:
        await admin_bot.bot.delete_webhook()
        await admin_bot.stop()
    if student_bot:
        await student_bot.bot.delete_webhook()
        await student_bot.stop()
    logger.info("🛑 Bots stopped and webhooks deleted")

app = FastAPI(
    title="Bourhan Teacher AI",
    version="1.0.0",
    lifespan=lifespan
)

# ---------- نقاط نهاية Webhooks ----------
@app.post("/webhook/admin")
async def admin_webhook(request: Request):
    """استقبال تحديثات بوت الأستاذ عبر Webhook"""
    if not admin_bot:
        return Response(status_code=404)
    
    try:
        data = await request.json()
        update = Update.de_json(data, admin_bot.bot)
        # معالجة التحديث عبر Application (يستخدم الـ handlers المسجلة)
        await admin_bot.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.exception(f"Admin webhook error: {e}")
        return Response(status_code=500)

@app.post("/webhook/student")
async def student_webhook(request: Request):
    """استقبال تحديثات بوت الطالب عبر Webhook"""
    if not student_bot:
        return Response(status_code=404)
    
    try:
        data = await request.json()
        update = Update.de_json(data, student_bot.bot)
        await student_bot.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.exception(f"Student webhook error: {e}")
        return Response(status_code=500)

# ---------- نقاط نهاية المراقبة ----------
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
