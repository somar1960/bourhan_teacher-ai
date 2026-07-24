import asyncio
import logging
from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.config import settings

# استيراد البوتات من أماكنها الجديدة
try:
    from app.bots.admin_bot.main import admin_bot
    from app.bots.student_bot.main import student_bot
except Exception as e:
    logging.error(f"خطأ في تحميل البوتات: {e}")
    admin_bot = None
    student_bot = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# هذه الدالة تشغل البوتات في الخلفية
async def start_bots():
    """تشغيل البوتات بشكل متزامن"""
    tasks = []
    if admin_bot:
        logger.info("🚀 بدء تشغيل بوت الأستاذ...")
        tasks.append(asyncio.create_task(admin_bot.run_polling()))
    if student_bot:
        logger.info("🚀 بدء تشغيل بوت الطالب...")
        tasks.append(asyncio.create_task(student_bot.run_polling()))
    
    if tasks:
        await asyncio.gather(*tasks)  # يشتغلون مع بعض
    else:
        logger.warning("⚠️ لا يوجد بوتات للاشتغال!")

# هذا الحدث يشتغل تلقائياً لما يبدأ السيرفر
@asynccontextmanager
async def lifespan(app: FastAPI):
    # هنا الكود اللي يشتغل عند بداية البرنامج
    logger.info("🔄 جارٍ تشغيل البوتات...")
    asyncio.create_task(start_bots())  # صحينا البوتات!
    yield
    # هنا الكود اللي يشتغل عند إيقاف البرنامج (مثل تنظيف)

# أنشئ التطبيق مع دورة الحياة
app = FastAPI(
    title="Bourhan Teacher AI",
    description="AI Educational Platform for Teachers and Students",
    version="1.0.0",
    lifespan=lifespan  # <-- هذا السطر هو الجديد والسحري!
)

# باقي المسارات حقك (زي ما هي)
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
    return {
        "status": "ok",
        "service": "Bourhan Teacher AI"
    }
