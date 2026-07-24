import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.student import Student

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = settings.student_bot_token
if not TOKEN:
    raise ValueError("student_bot_token غير موجود!")

student_bot = Application.builder().token(TOKEN).build()

# حالة انتظار إدخال رقم الهاتف
WAITING_PHONE = 1

# ------------------- دالة مساعدة للقائمة الرئيسية -------------------
def get_main_menu_keyboard():
    keyboard = [
        [InlineKeyboardButton("📚 ملفاتي", callback_data="my_files")],
        [InlineKeyboardButton("📝 واجباتي", callback_data="homework")],
        [InlineKeyboardButton("📅 مواعيدي", callback_data="schedule")],
        [InlineKeyboardButton("📢 الإعلانات", callback_data="announcements")],
        [InlineKeyboardButton("📊 علاماتي", callback_data="grades")],
        [InlineKeyboardButton("📈 مستواي", callback_data="level")],
        [InlineKeyboardButton("🎓 خطة اليوم", callback_data="daily")],
        [InlineKeyboardButton("🧠 المعلم الذكي", callback_data="ai")],
        [InlineKeyboardButton("⚙️ حسابي", callback_data="profile")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ------------------- أمر /start -------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # 1. نتحقق إذا كان الطالب مسجلاً بالفعل (telegram_id مربوط بحسابه)
    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.telegram_id == str(user_id))
        )
        student = result.scalar_one_or_none()
        
        if student:
            # موجود مسبقاً => نرحب به ونعرض القائمة
            await update.message.reply_text(
                f"👋 أهلاً بك مجدداً {student.name}!",
                reply_markup=get_main_menu_keyboard()
            )
            return
    
    # 2. إذا مش مسجل، نطلب رقم الهاتف
    await update.message.reply_text(
        "📱 مرحباً! يبدو أنك جديد هنا.\n"
        "الرجاء إدخال رقم هاتفك المسجل لدى الأستاذ (مثال: 0999123456):"
    )
    return WAITING_PHONE

# ------------------- استقبال رقم الهاتف -------------------
async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    user_id = update.effective_user.id
    
    # البحث عن الطالب في قاعدة البيانات
    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.phone == phone)
        )
        student = result.scalar_one_or_none()
        
        if not student:
            await update.message.reply_text(
                "❌ رقم الهاتف غير موجود في سجلات الأستاذ.\n"
                "تأكد من الرقم أو تواصل مع الأستاذ."
            )
            return WAITING_PHONE  # نطلب منه إعادة المحاولة
        
        # إذا وُجد الطالب، نربط حسابه بتلغرام
        student.telegram_id = str(user_id)
        await session.commit()
        
        await update.message.reply_text(
            f"✅ تم التحقق بنجاح! أهلاً بك {student.name} 🎉",
            reply_markup=get_main_menu_keyboard()
        )
        return ConversationHandler.END

# ------------------- إلغاء العملية -------------------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم إلغاء العملية.")
    return ConversationHandler.END

# ------------------- معالجة الأزرار (القائمة) -------------------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    # هنا نتحقق إذا كان الطالب مسجلاً
    user_id = update.effective_user.id
    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.telegram_id == str(user_id))
        )
        student = result.scalar_one_or_none()
        if not student:
            await query.message.reply_text("⛔ يرجى إعادة تشغيل البوت باستخدام /start")
            return
    
    # الردود المؤقتة على الأزرار (سنطورها لاحقاً)
    responses = {
        "my_files": "📚 ملفاتك: (سيتم إضافتها قريباً)",
        "homework": "📝 واجباتك: (سيتم إضافتها قريباً)",
        "schedule": "📅 مواعيدك: (سيتم إضافتها قريباً)",
        "announcements": "📢 الإعلانات: (سيتم إضافتها قريباً)",
        "grades": "📊 علاماتك: (سيتم إضافتها قريباً)",
        "level": "📈 مستواك: (سيتم إضافته قريباً)",
        "daily": "🎓 خطة اليوم: (سيتم إضافتها قريباً)",
        "ai": "🧠 المعلم الذكي: اكتب سؤالك وسأجيبك (قريباً)",
        "profile": f"👤 حسابك: {student.name}\n📞 {student.phone}",
    }
    
    await query.edit_message_text(
        responses.get(query.data, "خيار غير معروف"),
        reply_markup=get_main_menu_keyboard()  # يبقي القائمة ظاهرة
    )

# ------------------- تسجيل المعالج والمحادثة -------------------
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        WAITING_PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

student_bot.add_handler(conv_handler)
student_bot.add_handler(CallbackQueryHandler(button_callback))

logger.info("✅ Student bot initialized and ready!")
