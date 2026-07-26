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
    
    # ✅ القائمة الكاملة كما هو مطلوب في المشروع
    keyboard = [
        [InlineKeyboardButton("👨‍🎓 إدارة الطلاب", callback_data="students")],
        [InlineKeyboardButton("👥 المجموعات", callback_data="groups")],
        [InlineKeyboardButton("📚 إرسال ملفات", callback_data="files")],
        [InlineKeyboardButton("📢 الإعلانات", callback_data="announcements")],
        [InlineKeyboardButton("📝 الامتحانات", callback_data="exams")],
        [InlineKeyboardButton("📊 النتائج", callback_data="results")],
        [InlineKeyboardButton("📈 الإحصائيات", callback_data="statistics")],
        [InlineKeyboardButton("🧠 تدريب الذكاء الاصطناعي", callback_data="train_ai")],
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

# ---------- دوال مؤقتة لباقي الأزرار ----------
async def groups(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👥 **المجموعات**\n(سيتم إضافة هذه الميزة قريباً)")

async def files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📚 **إرسال ملفات**\n(سيتم إضافة هذه الميزة قريباً)")

async def announcements(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📢 **الإعلانات**\n(سيتم إضافة هذه الميزة قريباً)")

async def exams(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📝 **الامتحانات**\n(سيتم إضافة هذه الميزة قريباً)")

async def results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📊 **النتائج**\n(سيتم إضافة هذه الميزة قريباً)")

async def statistics(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📈 **الإحصائيات**\n(سيتم إضافة هذه الميزة قريباً)")

async def train_ai(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🧠 **تدريب الذكاء الاصطناعي**\n(سيتم إضافة هذه الميزة قريباً)")

async def settings_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚙️ **الإعدادات**\n(سيتم إضافة هذه الميزة قريباً)")

# ---------- معالج الأزرار ----------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    if user_id != settings.owner_telegram_id:
        await query.message.reply_text("⛔ هذا البوت للأستاذ فقط.")
        return

    data = query.data
    if data == "students":
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
    else:
        # رسائل مؤقتة لباقي الأزرار
        responses = {
            "groups": "👥 المجموعات: قريباً",
            "files": "📚 الملفات: قريباً",
            "announcements": "📢 الإعلانات: قريباً",
            "exams": "📝 الامتحانات: قريباً",
            "results": "📊 النتائج: قريباً",
            "statistics": "📈 الإحصائيات: قريباً",
            "train_ai": "🧠 تدريب الذكاء الاصطناعي: قريباً",
            "settings": "⚙️ الإعدادات: قريباً",
        }
        await query.message.reply_text(responses.get(data, "❌ خيار غير معروف"))

# ---------- تسجيل الأوامر ----------
admin_bot.add_handler(CommandHandler("start", start))
admin_bot.add_handler(CommandHandler("students", show_students))
admin_bot.add_handler(CommandHandler("add_student", add_student))
admin_bot.add_handler(CommandHandler("groups", groups))
admin_bot.add_handler(CommandHandler("files", files))
admin_bot.add_handler(CommandHandler("announcements", announcements))
admin_bot.add_handler(CommandHandler("exams", exams))
admin_bot.add_handler(CommandHandler("results", results))
admin_bot.add_handler(CommandHandler("statistics", statistics))
admin_bot.add_handler(CommandHandler("train_ai", train_ai))
admin_bot.add_handler(CommandHandler("settings", settings_command))
admin_bot.add_handler(CallbackQueryHandler(button_callback))

logger.info("✅ Admin bot with full menu ready!")
