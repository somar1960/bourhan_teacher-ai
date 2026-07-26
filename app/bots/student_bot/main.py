import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.student import Student, StudentTrack, StudentLevel
from app.services.ai_service import get_ai_response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = settings.student_bot_token
if not TOKEN:
    raise ValueError("student_bot_token غير موجود!")

# ---------- بناء البوت مع دعم الوكيل ----------
builder = Application.builder().token(TOKEN)
if settings.telegram_proxy:
    builder = builder.proxy(settings.telegram_proxy)
student_bot = builder.build()

# ---------- الثوابت ----------
TRACK_MAP = {
    "track_scientific": StudentTrack.SCIENTIFIC,
    "track_literary": StudentTrack.LITERARY,
    "track_conversation": StudentTrack.CONVERSATION,
}
TRACK_DISPLAY_NAMES = {
    StudentTrack.SCIENTIFIC: "العلمي",
    StudentTrack.LITERARY: "الأدبي",
    StudentTrack.CONVERSATION: "محادثات عامة"
}
PHONE_STATE = 1

# ---------- عرض القائمة حسب المسار ----------
async def show_main_menu(message, student):
    if student.track == StudentTrack.CONVERSATION:
        keyboard = [
            [InlineKeyboardButton("💬 المحادثات الذكية", callback_data="ai_chat")],
            [InlineKeyboardButton("📚 ملفاتي", callback_data="my_files")],
            [InlineKeyboardButton("⚙️ حسابي", callback_data="profile")],
        ]
        text = "🌐 **وضع المحادثات العامة**\nاسألني أي شيء عن اللغة الإنجليزية!"
    else:
        track_name = TRACK_DISPLAY_NAMES.get(student.track, "علمي")
        keyboard = [
            [InlineKeyboardButton("📚 ملفاتي", callback_data="my_files")],
            [InlineKeyboardButton("📝 واجباتي", callback_data="homework")],
            [InlineKeyboardButton("📢 الإعلانات", callback_data="announcements")],
            [InlineKeyboardButton("📊 علاماتي", callback_data="grades")],
            [InlineKeyboardButton("📈 مستواي", callback_data="level")],
            [InlineKeyboardButton("💬 المعلم الذكي", callback_data="ai_chat")],
            [InlineKeyboardButton("⚙️ حسابي", callback_data="profile")],
        ]
        text = f"🎓 **المسار: {track_name}**\nاختر من القائمة:"
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

# ---------- أمر /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.telegram_id == str(user_id))
        )
        student = result.scalar_one_or_none()
        if student:
            await show_main_menu(update.message, student)
            return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("🧪 علمي (منهج)", callback_data="track_scientific")],
        [InlineKeyboardButton("📖 أدبي (منهج)", callback_data="track_literary")],
        [InlineKeyboardButton("💬 محادثات عامة", callback_data="track_conversation")],
    ]
    await update.message.reply_text(
        "🎓 **مرحباً! اختر مسارك في اللغة الإنجليزية:**\n\n"
        "• **علمي**: دروس مركزة على المصطلحات العلمية.\n"
        "• **أدبي**: دروس مركزة على القواعد والأدب.\n"
        "• **محادثات عامة**: تدريب على المحادثة اليومية.",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )
    return ConversationHandler.END

# ---------- حفظ المسار ----------
async def save_track(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    track = TRACK_MAP.get(query.data)
    if not track:
        await query.message.reply_text("❌ خيار غير معروف.")
        return ConversationHandler.END

    context.user_data['temp_track'] = track
    await query.message.reply_text("📱 يرجى إدخال رقم هاتفك (كما هو مسجل لدى الأستاذ):")
    return PHONE_STATE

# ---------- استقبال رقم الهاتف ----------
async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    user_id = update.effective_user.id
    track = context.user_data.get('temp_track', StudentTrack.CONVERSATION)

    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.phone == phone)
        )
        student = result.scalar_one_or_none()
        if not student:
            await update.message.reply_text("❌ رقم غير مسجل. تواصل مع الأستاذ.")
            return PHONE_STATE
        
        student.telegram_id = str(user_id)
        student.track = track
        if not student.level:
            student.level = StudentLevel.UNKNOWN
        await session.commit()
        
        track_name = TRACK_DISPLAY_NAMES.get(track, "محادثات")
        await update.message.reply_text(f"✅ تم التسجيل في مسار {track_name}!")
        await show_main_menu(update.message, student)
        
    return ConversationHandler.END

# ---------- المعلم الذكي ----------
async def ai_chat_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query:
        await query.answer()
        message = query.message
    else:
        message = update.message

    user_id = update.effective_user.id
    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.telegram_id == str(user_id))
        )
        student = result.scalar_one_or_none()
        if not student:
            await message.reply_text("⚠️ يرجى إعادة تشغيل البوت بـ /start")
            return
        context.user_data['student_id'] = student.id
        context.user_data['ai_mode'] = True

    await message.reply_text(
        "🧠 **المعلم الذكي جاهز!**\n\n"
        "اكتب سؤالك عن أي قاعدة، وسأشرحها لك.\n"
        "لإنهاء المحادثة، اكتب /exit_ai"
    )

async def ai_chat_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('ai_mode', False):
        return
    
    question = update.message.text
    student_id = context.user_data.get('student_id')
    if not student_id:
        await update.message.reply_text("⚠️ يرجى إعادة تشغيل البوت بـ /start")
        return

    await update.message.reply_text("⏳ جاري التفكير...")
    try:
        answer = await get_ai_response(student_id, question)
        await update.message.reply_text(answer, parse_mode="Markdown")
    except Exception as e:
        logger.exception(f"خطأ في الذكاء الاصطناعي: {e}")
        await update.message.reply_text("❌ حدث خطأ. حاول مجدداً لاحقاً.")

async def ai_chat_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ai_mode'] = False
    await update.message.reply_text("👋 تم الخروج من المعلم الذكي. استخدم /start للرجوع للقائمة.")

# ---------- معالج الأزرار العامة ----------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "ai_chat":
        await ai_chat_start(update, context)
    else:
        responses = {
            "my_files": "📚 ملفاتك: (سيتم إضافتها قريباً)",
            "homework": "📝 واجباتك: (سيتم إضافتها قريباً)",
            "announcements": "📢 الإعلانات: (سيتم إضافتها قريباً)",
            "grades": "📊 علاماتك: (سيتم إضافتها قريباً)",
            "level": "📈 مستواك: (سيتم إضافته قريباً)",
            "profile": "👤 حسابك: (سيتم إضافته قريباً)",
        }
        await query.edit_message_text(responses.get(data, "❌ خيار غير معروف"))

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم الإلغاء.")
    return ConversationHandler.END

# ---------- تسجيل المعالجات ----------
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        PHONE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

student_bot.add_handler(conv_handler)
student_bot.add_handler(CallbackQueryHandler(save_track, pattern="^track_"))
student_bot.add_handler(CallbackQueryHandler(button_callback, pattern="^(?!track_).*"))
student_bot.add_handler(CommandHandler("exit_ai", ai_chat_exit))
student_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handle))

logger.info("✅ Student bot with track selection and proxy support ready!")
