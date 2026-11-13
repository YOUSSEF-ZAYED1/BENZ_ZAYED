"""
🚗 Mercedes Telegram Bot - نقطة الدخول الرئيسية
البوت ده بيدير اشتراكات وبرامج مرسيدس عن طريق تليجرام
"""

import logging
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, BotCommand, BotCommandScopeChat, MenuButtonCommands
from telegram.ext import ApplicationBuilder

# استيراد الإعدادات وقاعدة البيانات
from config import BOT_TOKEN, ADMIN_IDS
from database import init_db

# استيراد دوال تسجيل الهاندلرز
from handlers.start import register_start_handlers
from handlers.programs import register_program_handlers
from handlers.subscription import register_subscription_handlers
from handlers.admin import register_admin_handlers

# إعداد اللوجينج عشان نتابع اللي بيحصل في البوت
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


class HealthHandler(BaseHTTPRequestHandler):
    """سيرفر فحص بسيط عشان الاستضافات السحابية المجانية (Render/Koyeb) تفضل شغالة 24/7"""
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Mercedes Bot is running 24/7!")

    def log_message(self, format, *args):
        return  # منع اللوجات الكتير من الفحص


def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthHandler)
    server.serve_forever()


async def post_init(application) -> None:
    """تحديث قائمة الأوامر وزرار المنيو في تليجرام تلقائياً عند التشغيل"""
    user_commands = [
        BotCommand("start", "ابدأ البوت / Start bot"),
        BotCommand("help", "المساعدة / Help"),
        BotCommand("about", "عن البوت / About"),
    ]
    await application.bot.set_my_commands(user_commands)
    await application.bot.set_chat_menu_button(menu_button=MenuButtonCommands())

    admin_commands = user_commands + [
        BotCommand("admin", "لوحة تحكم الأدمن / Admin Panel"),
    ]
    for admin_id in ADMIN_IDS:
        try:
            await application.bot.set_my_commands(
                admin_commands,
                scope=BotCommandScopeChat(chat_id=admin_id),
            )
        except Exception as e:
            logger.warning("تعذر ضبط أوامر الأدمن %s: %s", admin_id, e)


async def error_handler(update: object, context) -> None:
    """هاندلر الأخطاء العام - بيسجل أي إيرور بيحصل في البوت"""
    logger.error("حصل إيرور أثناء معالجة التحديث:", exc_info=context.error)


def main() -> None:
    """الفانكشن الرئيسية - بتشغل البوت"""
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error(
            "❌ توكن البوت مش متضاف! اعمل ملف .env (من .env.example) وحط فيه BOT_TOKEN بتاعك من @BotFather."
        )
        sys.exit(1)

    # تهيئة قاعدة البيانات وإضافة برامج مرسيدس الافتراضية
    init_db()
    logger.info("✅ قاعدة البيانات اتهيأت بنجاح")

    # تشغيل سيرفر الفحص في الخلفية لاستضافات الكلاود المجانية (زي Render)
    try:
        threading.Thread(target=start_health_server, daemon=True).start()
        logger.info("🌐 سيرفر الفحص (Health Server) شغال في الخلفية")
    except Exception as e:
        logger.warning("تعذر تشغيل سيرفر الفحص: %s", e)

    # بناء التطبيق باستخدام التوكن من الإعدادات
    application = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # ─── تسجيل الهاندلرز بالترتيب الصحيح ───
    # 1) هاندلرز الأدمن الأول (عشان فيها ConversationHandlers لازم تاخد أولوية على الرسائل العامة)
    register_admin_handlers(application)
    # 2) هاندلرز البداية والقوائم
    register_start_handlers(application)
    # 3) هاندلرز البرامج والملفات
    register_program_handlers(application)
    # 4) هاندلرز الاشتراكات والدفع (فيها MessageHandler عام للصور/النصوص وقت انتظار الإثبات)
    register_subscription_handlers(application)

    # ─── هاندلر الأخطاء ───
    application.add_error_handler(error_handler)

    # تشغيل البوت بالـ polling
    logger.info("🚗 Mercedes Bot شغال وجاهز!")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
