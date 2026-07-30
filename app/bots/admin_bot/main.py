"""
Admin bot for Bourhan Teacher AI.
Factory function returning a ptb Application for teacher actions.
"""

from __future__ import annotations

import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from sqlalchemy import select

from app.config import settings
from app.database import async_session
from app.models.student import Student

logger = logging.getLogger(__name__)


def create_admin_bot() -> Application:
    """
    Creates and configures the admin Telegram bot.

    Returns:
        A fully configured ptb Application.
    """

    # ---------- دوال التحقق من الصلاحية ----------
    async def is_owner(update: Update) -> bool:
        user_id = update.effective_user.id
        if user_id == settings.owner_telegram_id:
            return True
        if update.message:
            await update.message.reply_text(
                "⛔ عذراً، هذا البوت مخصص للأستاذ فقط."
            )
        elif update.callback_query:
            await update.callback_query.answer(
                "هذا البوت للأستاذ فقط.",
                show_alert=True
            )
        return False

    # ---------- الأوامر ----------
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await is_owner(update):
            return
        
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
                    status = "✅ مفعل" if s.is_approved else "⏳ قيد المراجعة"
                    reply += f"• {s.name} - 📞 {s.phone} - {status}\n"
                await update.message.reply_text(reply, parse_mode="Markdown")
            except Exception as e:
                logger.exception(f"خطأ في جلب الطلاب: {e}")
                await update.message.reply_text(f"❌ خطأ في قاعدة البيانات: {str(e)}")

    async def add_student(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not await is_owner(update):
            return
        args = context.args
        if len(args) < 2:
            await update.message.reply_text(
                "➕ لإضافة طالب، استخدم الأمر:\n"
                "/add_student الاسم رقم_الهاتف\n"
                "مثال: /add_student أحمد 0999123456"
            )
            return
        
        name = args[0]
        phone = args[1]
        
        async with async_session() as session:
            # التحقق من عدم وجود الرقم
            result = await session.execute(
                select(Student).where(Student.phone == phone)
            )
            existing = result.scalar_one_or_none()
            if existing:
                await update.message.reply_text("⚠️ هذا الرقم مسجل بالفعل.")
                return
            
            new_student = Student(
                name=name,
                phone=phone,
                is_approved=True  # عند الإضافة اليدوية، يُفعل فوراً
            )
            session.add(new_student)
            await session.commit()
            await update.message.reply_text(f"✅ تم إضافة الطالب {name} بنجاح!")

    # ---------- معالج طلبات التسجيل ----------
    async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """معالجة قبول أو رفض الطالب"""
        query = update.callback_query
        await query.answer()
        
        data = query.data
        student_id = int(data.split('_')[1])
        action = data.split('_')[0]
        
        async with async_session() as session:
            result = await session.execute(
                select(Student).where(Student.id == student_id)
            )
            student = result.scalar_one_or_none()
            if not student:
                await query.edit_message_text("❌ الطالب غير موجود.")
                return
            
            if action == "approve":
                student.is_approved = True
                await session.commit()
                await query.edit_message_text(f"✅ تم قبول الطالب {student.name}!")
                
                # إرسال رسالة للطالب عبر البوت الحالي
                try:
                    await context.application.bot.send_message(
                        chat_id=int(student.telegram_id),
                        text="🎉 **تم قبول طلبك!**\nيمكنك الآن استخدام البوت بالكامل. أرسل /start للبدء."
                    )
                except Exception as e:
                    logger.warning(f"لم نتمكن من إرسال رسالة للطالب {student.telegram_id}: {e}")
                    
            else:  # reject
                await session.delete(student)
                await session.commit()
                await query.edit_message_text(f"❌ تم رفض الطالب {student.name}.")
                
                # إرسال رسالة للطالب عبر البوت الحالي
                try:
                    await context.application.bot.send_message(
                        chat_id=int(student.telegram_id),
                        text="❌ **للأسف، تم رفض طلبك.** يرجى التواصل مع الأستاذ للاستفسار."
                    )
                except Exception as e:
                    logger.warning(f"لم نتمكن من إرسال رسالة للطالب {student.telegram_id}: {e}")

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
                    status = "✅ مفعل" if s.is_approved else "⏳ قيد المراجعة"
                    reply += f"• {s.name} - {s.phone} - {status}\n"
                await query.message.reply_text(reply, parse_mode="Markdown")
        else:
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

    # ------------------------------------------------------------------
    # Build the Application
    # ------------------------------------------------------------------
    builder = Application.builder().token(settings.admin_bot_token)
    if settings.telegram_proxy:
        builder = builder.proxy(settings.telegram_proxy)
    application = builder.build()

    # ---------- تسجيل المعالجات ----------
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("students", show_students))
    application.add_handler(CommandHandler("add_student", add_student))
    application.add_handler(CommandHandler("groups", groups))
    application.add_handler(CommandHandler("files", files))
    application.add_handler(CommandHandler("announcements", announcements))
    application.add_handler(CommandHandler("exams", exams))
    application.add_handler(CommandHandler("results", results))
    application.add_handler(CommandHandler("statistics", statistics))
    application.add_handler(CommandHandler("train_ai", train_ai))
    application.add_handler(CommandHandler("settings", settings_command))

    # ترتيب الـ CallbackQueryHandler مهم: handle_approval أولاً لأن نمطه أكثر تحديداً
    application.add_handler(
        CallbackQueryHandler(handle_approval, pattern="^(approve|reject)_")
    )
    application.add_handler(
        CallbackQueryHandler(
            button_callback,
            pattern="^(students|groups|files|announcements|exams|results|statistics|train_ai|settings)$"
        )
    )

    logger.info("Admin bot factory configured successfully.")
    return application