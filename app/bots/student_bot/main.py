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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = settings.student_bot_token
if not TOKEN:
    raise ValueError("student_bot_token غير موجود!")

# بناء التطبيق (بدون تشغيل)
builder = Application.builder().token(TOKEN)
if settings.telegram_proxy:
    builder = builder.proxy(settings.telegram_proxy)
student_bot = builder.build()

# ---------- حالات المحادثة ----------
NAME_STATE, PHONE_STATE, TRACK_STATE = range(1, 4)

# ---------- دوال مساعدة ----------
async def show_main_menu(message, student):
    """عرض القائمة حسب المسار"""
    if student.track == StudentTrack.CONVERSATION:
        keyboard = [
            [InlineKeyboardButton("🧠 المعلم الذكي", callback_data="ai_chat")],
            [InlineKeyboardButton("📚 ملفاتي", callback_data="my_files")],
            [InlineKeyboardButton("⚙️ حسابي", callback_data="profile")],
        ]
        text = "🌐 **وضع المحادثات العامة**\nاسألني أي شيء عن اللغة الإنجليزية!"
    else:
        track_name = "العلمي" if student.track == StudentTrack.SCIENTIFIC else "الأدبي"
        keyboard = [
            [InlineKeyboardButton("📚 ملفاتي", callback_data="my_files")],
            [InlineKeyboardButton("📝 واجباتي", callback_data="homework")],
            [InlineKeyboardButton("📅 مواعيدي", callback_data="schedule")],
            [InlineKeyboardButton("📢 الإعلانات", callback_data="announcements")],
            [InlineKeyboardButton("📊 علاماتي", callback_data="grades")],
            [InlineKeyboardButton("📈 مستواي", callback_data="level")],
            [InlineKeyboardButton("🎓 خطة اليوم", callback_data="daily_plan")],
            [InlineKeyboardButton("🧠 المعلم الذكي", callback_data="ai_chat")],
            [InlineKeyboardButton("⚙️ حسابي", callback_data="profile")],
        ]
        text = f"🎓 **المسار: {track_name}**\nاختر من القائمة:"
    
    await message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def notify_admin(student_id: int, name: str, phone: str, track: str):
    """إرسال طلب التسجيل إلى بوت الأستاذ"""
    admin_bot_token = settings.admin_bot_token
    admin_id = settings.owner_telegram_id
    
    # إنشاء تطبيق مؤقت لإرسال الرسالة للأستاذ
    app = Application.builder().token(admin_bot_token).build()
    await app.initialize()
    
    keyboard = [
        [
            InlineKeyboardButton("✅ قبول", callback_data=f"approve_{student_id}"),
            InlineKeyboardButton("❌ رفض", callback_data=f"reject_{student_id}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    track_name = "علمي" if track == StudentTrack.SCIENTIFIC else "أدبي" if track == StudentTrack.LITERARY else "محادثات"
    message = (
        f"📢 **طلب تسجيل جديد:**\n"
        f"👤 الاسم: {name}\n"
        f"📞 الهاتف: {phone}\n"
        f"📚 المسار: {track_name}\n"
        f"🆔 ID: {student_id}"
    )
    
    await app.bot.send_message(
        chat_id=admin_id,
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )
    await app.shutdown()

# ---------- أمر /start ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.telegram_id == str(user_id))
        )
        student = result.scalar_one_or_none()
        
        if student:
            if student.is_approved:
                await show_main_menu(update.message, student)
                return ConversationHandler.END
            else:
                await update.message.reply_text(
                    "⏳ طلبك لا يزال قيد المراجعة من قبل الأستاذ. يرجى الانتظار."
                )
                return ConversationHandler.END

    # إذا لم يكن مسجلاً، ابدأ طلب الاسم
    await update.message.reply_text(
        "📝 **مرحباً! يرجى إدخال اسمك الثلاثي (الاسم الكامل):**"
    )
    return NAME_STATE

# ---------- استقبال الاسم ----------
async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    if len(name) < 3:
        await update.message.reply_text("⚠️ يرجى إدخال اسم صحيح (ثلاثي على الأقل).")
        return NAME_STATE
    context.user_data['temp_name'] = name
    await update.message.reply_text(
        "📱 **يرجى إدخال رقم هاتفك السوري (مثال: 0999123456):**"
    )
    return PHONE_STATE

# ---------- استقبال رقم الهاتف ----------
async def receive_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    phone = update.message.text.strip()
    # تحقق بسيط من الرقم (10 أرقام تبدأ بـ 09)
    if not (phone.isdigit() and len(phone) == 10 and phone.startswith('09')):
        await update.message.reply_text(
            "⚠️ رقم غير صحيح. يرجى إدخال 10 أرقام تبدأ بـ 09 (مثال: 0999123456)."
        )
        return PHONE_STATE
    
    # التحقق من عدم تكرار الرقم
    async with async_session() as session:
        result = await session.execute(
            select(Student).where(Student.phone == phone)
        )
        existing = result.scalar_one_or_none()
        if existing:
            await update.message.reply_text(
                "⚠️ هذا الرقم مسجل بالفعل. يرجى التواصل مع الأستاذ."
            )
            return PHONE_STATE
    
    context.user_data['temp_phone'] = phone
    # عرض أزرار اختيار المسار
    keyboard = [
        [InlineKeyboardButton("🧪 علمي", callback_data="track_scientific")],
        [InlineKeyboardButton("📖 أدبي", callback_data="track_literary")],
        [InlineKeyboardButton("💬 محادثات عامة", callback_data="track_conversation")],
    ]
    await update.message.reply_text(
        "🎓 **اختر مسارك التعليمي:**",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return TRACK_STATE

# ---------- حفظ المسار وإرسال الطلب ----------
async def save_track_and_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    
    track_map = {
        "track_scientific": StudentTrack.SCIENTIFIC,
        "track_literary": StudentTrack.LITERARY,
        "track_conversation": StudentTrack.CONVERSATION,
    }
    track = track_map.get(query.data)
    if not track:
        await query.message.reply_text("❌ خيار غير معروف.")
        return ConversationHandler.END
    
    name = context.user_data.get('temp_name')
    phone = context.user_data.get('temp_phone')
    
    # حفظ الطالب في قاعدة البيانات (غير مفعل حتى قبول الأستاذ)
    async with async_session() as session:
        new_student = Student(
            name=name,
            phone=phone,
            telegram_id=str(user_id),
            track=track,
            level=StudentLevel.UNKNOWN,
            is_approved=False
        )
        session.add(new_student)
        await session.commit()
        await session.refresh(new_student)
        student_id = new_student.id
    
    # إرسال طلب إلى الأستاذ
    await notify_admin(student_id, name, phone, track)
    
    await query.message.reply_text(
        "✅ **تم إرسال طلبك إلى الأستاذ بنجاح!**\n"
        "سيتم إعلامك عند الموافقة على طلبك."
    )
    return ConversationHandler.END

# ---------- معالج الأزرار العامة ----------
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "ai_chat":
        # بدء المحادثة مع الذكاء الاصطناعي
        user_id = update.effective_user.id
        async with async_session() as session:
            result = await session.execute(
                select(Student).where(Student.telegram_id == str(user_id))
            )
            student = result.scalar_one_or_none()
            if not student or not student.is_approved:
                await query.message.reply_text(
                    "⚠️ حسابك غير مفعل. يرجى الانتظار حتى يوافق الأستاذ."
                )
                return
            context.user_data['student_id'] = student.id
            context.user_data['ai_mode'] = True
        await query.message.reply_text(
            "🧠 **المعلم الذكي جاهز!**\n"
            "اكتب سؤالك، لإنهاء المحادثة اكتب /exit_ai"
        )
        return

    # رسائل مؤقتة لباقي الأزرار
    responses = {
        "my_files": "📚 **ملفاتي** (سيتم إضافتها قريباً)",
        "homework": "📝 **واجباتي** (سيتم إضافتها قريباً)",
        "schedule": "📅 **مواعيدي** (سيتم إضافتها قريباً)",
        "announcements": "📢 **الإعلانات** (سيتم إضافتها قريباً)",
        "grades": "📊 **علاماتي** (سيتم إضافتها قريباً)",
        "level": "📈 **مستواي** (سيتم إضافته قريباً)",
        "daily_plan": "🎓 **خطة اليوم** (سيتم إضافتها قريباً)",
        "profile": "👤 **حسابي** (سيتم إضافته قريباً)",
    }
    await query.edit_message_text(
        responses.get(data, "❌ خيار غير معروف"),
        parse_mode="Markdown"
    )

# ---------- الخروج من المعلم الذكي ----------
async def ai_chat_exit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['ai_mode'] = False
    await update.message.reply_text("👋 تم الخروج من المعلم الذكي.")

# ---------- معالج رسائل الذكاء الاصطناعي ----------
async def ai_chat_handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get('ai_mode', False):
        return
    # TODO: ربط الذكاء الاصطناعي هنا لاحقاً
    await update.message.reply_text(
        "⏳ جاري التفكير... (سيتم إضافة الذكاء الاصطناعي قريباً)"
    )

# ---------- إلغاء العملية ----------
async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ تم الإلغاء.")
    return ConversationHandler.END

# ---------- تسجيل المعالجات ----------
conv_handler = ConversationHandler(
    entry_points=[CommandHandler("start", start)],
    states={
        NAME_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
        PHONE_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_phone)],
        TRACK_STATE: [CallbackQueryHandler(save_track_and_request, pattern="^track_")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
)

student_bot.add_handler(conv_handler)
student_bot.add_handler(CallbackQueryHandler(button_callback, pattern="^(?!track_).*"))
student_bot.add_handler(CommandHandler("exit_ai", ai_chat_exit))
student_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handle))

logger.info("✅ Student bot registration flow updated!")