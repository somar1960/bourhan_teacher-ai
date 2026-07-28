import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from app.config import settings
from app.database import async_session, create_tables

try:
    from app.bots.admin_bot.main import admin_bot
    from app.bots.student_bot.main import student_bot
except Exception:
    logging.exception("خطأ في تحميل البوتات")
    admin_bot = None
    student_bot = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_bot_in_thread(bot, bot_name: str):
    """تشغيل البوت في خيط منفصل"""

    def start_bot():
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # حذف أي Webhook قديم
            loop.run_until_complete(
                bot.bot.delete_webhook(drop_pending_updates=True)
            )

            # تشغيل البوت بطريقة Polling
            loop.run_until_complete(
                bot.run_polling(stop_signals=None)
            )

        except Exception as e:
            logger.exception(f"❌ {bot_name} error: {e}")

        finally:
            loop.close()

    await asyncio.to_thread(start_bot)


@asynccontextmanager
async def lifespan(app: FastAPI):

    # ✅ إنشاء جميع الجداول إذا لم تكن موجودة
    try:
        await create_tables()
        logger.info("✅ Database tables checked")
    except Exception as e:
        logger.exception(f"❌ Database initialization failed: {e}")

    tasks = []

    if admin_bot:
        task = asyncio.create_task(
            run_bot_in_thread(admin_bot, "Admin Bot")
        )
        tasks.append(task)
        logger.info("🚀 Admin Bot started")

    if student_bot:
        task = asyncio.create_task(
            run_bot_in_thread(student_bot, "Student Bot")
        )
        tasks.append(task)
        logger.info("🚀 Student Bot started")

    yield

    for task in tasks:
        task.cancel()

    await asyncio.gather(*tasks, return_exceptions=True)

    logger.info("🛑 Bots stopped")


app = FastAPI(
    title="Bourhan Teacher AI",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {
        "project": "Bourhan Teacher AI",
        "message": "Platform is running 🚀",
        "environment": settings.environment,
        "bots": {
            "admin": "active" if admin_bot else "inactive",
            "student": "active" if student_bot else "inactive",
        },
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

        return {
            "status": "db_error",
            "detail": str(e),
        }