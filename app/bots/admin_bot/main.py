import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.student import Student

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = settings.admin_bot_token
if not TOKEN:
    raise ValueError("admin_bot_token غير موجود!")

# ---------- بناء البوت مع دعم الوكيل ----------
builder = Application.builder().token(TOKEN)
if settings.telegram_proxy:
    builder = builder.proxy(settings.telegram_proxy)
admin_bot = builder.build()

# ---------- دوال التحقق من الصلاحية ----------
async def is_owner(update: Update) -> bool:
    user_id = update.effective_user.id
    if user_id != settings.owner_telegram_id:
        await update.message.reply_text("⛔ عذراً، هذا البوت مخصص للأستاذ فقط.")
        return False
    return True

# ---------- الأوامر ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_owner(update):
        return
    keyboard = [
        [InlineKeyboardButton("👨‍🎓 إدارة الطلاب", callback_data="students")],
        [InlineKeyboardButton("➕ إضافة طالب", callback_data="add_student")],
        [InlineKeyboardButton("⚙️ الإعدادات", callback_data="settings")],
    ]
    await update.message.reply_text(
        "👋 مرحباً أيها الأستاذ!\nاختر من القائمة:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_students(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_owner(update):
        return
    async with async_session() as session:
        try:
            result = await session.execute(select(Student).limit(20))
            students = result.scalars().all()
            if not students:
                await update.message.reply_text("📭 لا يوجد طلاب مسجلين.")
                return
            reply = "👨‍🎓 **قائمة الطلاب:**\n\n"
            for s in students:
                reply += f"• {s.name} - 📞 {s.phone}\n"
            await update.message.reply_text(reply, parse_mode="Markdown")
        except Exception as e:
            logger.exception(f"خطأ في جلب الطلاب: {e}")
            await update.message.reply_text(f"❌ خطأ في قاعدة البيانات: {str(e)}")

async def add_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_owner(update):
        return
    await update.message.reply_text(
        "➕ لإضافة طالب، استخدم الأمر:\n"
        "/add_student الاسم رقم_الهاتف\n"
        "مثال: /add_student أحمد 0999123456"
    )

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_owner(update):
        return
    await update.message.reply_text("⚙️ الإعدادات: قريباً")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    if user_id != settings.owner_telegram_id:
        await query.message.reply_text("⛔ هذا البوت للأستاذ فقط.")
        return

    if query.data == "students":
        async with async_session() as session:
            result = await session.execute(select(Student).limit(20))
            students = result.scalars().all()
            if not students:
                await query.message.reply_text("📭 لا يوجد طلاب.")
                return
            reply = "👨‍🎓 **الطلاب:**\n"
            for s in students:
                reply += f"• {s.name} - {s.phone}\n"
            await query.message.reply_text(reply, parse_mode="Markdown")
    elif query.data == "add_student":
        await query.message.reply_text("➕ أرسل: /add_student الاسم الهاتف")
    else:
        await query.message.reply_text("❌ خيار غير معروف")

# ---------- تسجيل الأوامر ----------
admin_bot.add_handler(CommandHandler("start", start))
admin_bot.add_handler(CommandHandler("students", show_students))
admin_bot.add_handler(CommandHandler("add_student", add_student))
admin_bot.add_handler(CommandHandler("settings", settings_command))
admin_bot.add_handler(CallbackQueryHandler(button_callback))

logger.info("✅ Admin bot secured and ready!")
