"""
Production main.py for Bourhan Teacher AI.
FastAPI + Telegram Webhooks (no polling) using the Factory Pattern.
"""

import os
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from sqlalchemy import text
from telegram import Update

from app.config import settings
from app.database import async_session
from app.bots.admin_bot.main import create_admin_bot
from app.bots.student_bot.main import create_student_bot

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Instantiate both bots using the Factory Pattern
# ---------------------------------------------------------------------------
admin_bot = create_admin_bot()
student_bot = create_student_bot(admin_bot)

# Webhook base URL (provided by Render automatically)
BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "https://bourhan-teacher-ai.onrender.com")
ADMIN_WEBHOOK_URL = f"{BASE_URL}/webhook/admin"
STUDENT_WEBHOOK_URL = f"{BASE_URL}/webhook/student"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI lifespan:
    - Initialise both bots
    - Set Telegram webhooks
    - On shutdown: delete webhooks and stop bots
    """
    # Startup
    await admin_bot.initialize()
    await student_bot.initialize()

    await admin_bot.bot.set_webhook(
        url=ADMIN_WEBHOOK_URL,
        drop_pending_updates=True,
    )
    logger.info("✅ Admin Webhook set to %s", ADMIN_WEBHOOK_URL)

    await student_bot.bot.set_webhook(
        url=STUDENT_WEBHOOK_URL,
        drop_pending_updates=True,
    )
    logger.info("✅ Student Webhook set to %s", STUDENT_WEBHOOK_URL)

    yield

    # Shutdown
    await admin_bot.bot.delete_webhook()
    await student_bot.bot.delete_webhook()
    await admin_bot.stop()
    await student_bot.stop()
    logger.info("🛑 Bots stopped and webhooks deleted")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Bourhan Teacher AI",
    version="1.0.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Webhook endpoints
# ---------------------------------------------------------------------------
@app.post("/webhook/admin")
async def admin_webhook(request: Request):
    """Receive Telegram updates for the admin bot."""
    try:
        data = await request.json()
        update = Update.de_json(data, admin_bot.bot)
        await admin_bot.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.exception("Admin webhook error: %s", e)
        return Response(status_code=500)


@app.post("/webhook/student")
async def student_webhook(request: Request):
    """Receive Telegram updates for the student bot."""
    try:
        data = await request.json()
        update = Update.de_json(data, student_bot.bot)
        await student_bot.process_update(update)
        return Response(status_code=200)
    except Exception as e:
        logger.exception("Student webhook error: %s", e)
        return Response(status_code=500)


# ---------------------------------------------------------------------------
# Health check endpoints
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {
        "project": "Bourhan Teacher AI",
        "message": "Platform is running 🚀",
        "environment": settings.environment,
        "bots": {
            "admin": "active",
            "student": "active",
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
        return {"status": "db_error", "detail": str(e)}