# utils/texts.py
# كل النصوص والرسائل بتاعة البوت بالعربي والإنجليزي

from typing import Dict

TEXTS: Dict[str, Dict[str, str]] = {
    # ─── رسائل الترحيب واللغة ───
    "welcome": {
        "ar": (
            "أهلاً بيك يا <b>{name}</b> في بوت برامج مرسيدس! 🚗✨\n\n"
            "من هنا تقدر تتصفح برامج مرسيدس (Xentry, DTS Monaco, Vediamo, EPC وغيرها)، "
            "تشترك، وتحمّل الملفات بالباسوورد الخاص بكل نسخة.\n\n"
            "اختار من القائمة تحت 👇"
        ),
        "en": (
            "Welcome <b>{name}</b> to Mercedes Software Bot! 🚗✨\n\n"
            "Browse Mercedes diagnostic & parts software (Xentry, DTS Monaco, Vediamo, EPC, etc.), "
            "subscribe, and download files with per-version passwords.\n\n"
            "Choose from the menu below 👇"
        ),
    },
    "language_set": {
        "ar": "✅ تم تغيير اللغة للعربي بنجاح!",
        "en": "✅ Language changed to English successfully!",
    },

    # ─── القوائم والأزرار ───
    "main_menu": {
        "ar": "📋 <b>القائمة الرئيسية</b>\n\nاختار من الاختيارات اللي تحت 👇",
        "en": "📋 <b>Main Menu</b>\n\nChoose from the options below 👇",
    },
    "btn_programs": {
        "ar": "📂 البرامج",
        "en": "📂 Programs",
    },
    "btn_my_subscription": {
        "ar": "📊 اشتراكي",
        "en": "📊 My Subscription",
    },
    "btn_subscribe": {
        "ar": "💳 اشتراك جديد",
        "en": "💳 Subscribe",
    },
    "btn_help": {
        "ar": "❓ المساعدة",
        "en": "❓ Help",
    },
    "btn_about": {
        "ar": "ℹ️ عن البوت",
        "en": "ℹ️ About",
    },
    "btn_contact_support": {
        "ar": "💬 تواصل مع الإدارة / الدعم",
        "en": "💬 Contact Admin / Support",
    },
    "btn_language": {
        "ar": "🌐 اللغة / Language",
        "en": "🌐 Language / اللغة",
    },
    "btn_back_menu": {
        "ar": "🔙 القائمة الرئيسية",
        "en": "🔙 Main Menu",
    },
    "btn_back_programs": {
        "ar": "🔙 رجوع للبرامج",
        "en": "🔙 Back to Programs",
    },
    "btn_download": {
        "ar": "تحميل الملف",
        "en": "Download File",
    },
    "btn_cancel": {
        "ar": "❌ إلغاء",
        "en": "❌ Cancel",
    },
    "btn_pay_online_card": {
        "ar": "💳 دفع فوري بالكارت (تليجرام)",
        "en": "💳 Pay Instantly by Card",
    },

    # ─── المساعدة وعن البوت ───
    "help_message": {
        "ar": (
            "❓ <b>المساعدة</b>\n\n"
            "• اضغط على <b>📂 البرامج</b> عشان تشوف البرامج المتاحة\n"
            "• اضغط على <b>💳 اشتراك جديد</b> عشان تشترك (شهري أو سنوي)\n"
            "• اضغط على <b>📊 اشتراكي</b> عشان تتابع حالة اشتراكك\n"
            "• بعد تفعيل الاشتراك تقدر تحمّل أي برنامج وتاخد باسوورد فك الضغط\n\n"
            "لو عندك أي استفسار تواصل مع الدعم: {support}"
        ),
        "en": (
            "❓ <b>Help</b>\n\n"
            "• Tap <b>📂 Programs</b> to browse available software\n"
            "• Tap <b>💳 Subscribe</b> to choose a plan (Monthly / Yearly)\n"
            "• Tap <b>📊 My Subscription</b> to check your status\n"
            "• Once active, you can download files and get the archive password\n\n"
            "Need help? Contact support: {support}"
        ),
    },
    "about_message": {
        "ar": (
            "ℹ️ <b>عن البوت</b>\n\n"
            "بوت مخصص لتوفير برامج تشخيص وبرمجة وكتالوجات مرسيدس بنز "
            "(Xentry, DTS Monaco, Vediamo, EPC/WIS وغيرها) بأحدث الإصدارات.\n\n"
            "🔐 كل نسخة محمية بباسوورد خاص بيتحدّث مع كل أبديت.\n"
            "📧 للدعم الفني: {support}"
        ),
        "en": (
            "ℹ️ <b>About</b>\n\n"
            "Specialized bot for Mercedes-Benz diagnostic, coding, and parts software "
            "(Xentry, DTS Monaco, Vediamo, EPC/WIS, and more).\n\n"
            "🔐 Every version has its own password updated per release.\n"
            "📧 Technical Support: {support}"
        ),
    },

    # ─── البرامج والملفات ───
    "programs_title": {
        "ar": "📂 <b>البرامج المتاحة</b>\n\nاختار البرنامج اللي عايز تفاصيله:",
        "en": "📂 <b>Available Programs</b>\n\nSelect a program to view details:",
    },
    "program_detail_template": {
        "ar": (
            "📦 <b>{name}</b>\n\n"
            "📝 <b>الوصف:</b> {description}\n"
            "📂 <b>التصنيف:</b> {category}\n"
            "🔢 <b>الإصدار:</b> {version}\n\n"
            "👇 اختر الملف للتحميل:"
        ),
        "en": (
            "📦 <b>{name}</b>\n\n"
            "📝 <b>Description:</b> {description}\n"
            "📂 <b>Category:</b> {category}\n"
            "🔢 <b>Version:</b> {version}\n\n"
            "👇 Choose a file to download:"
        ),
    },
    "download_info_template": {
        "ar": (
            "✅ <b>بيانات التحميل جاهزة!</b>\n\n"
            "📄 <b>الملف:</b> {file_name}\n"
            "🔢 <b>الإصدار:</b> {version}\n"
            "📦 <b>الحجم:</b> {size_info}\n\n"
            "🔗 <b>رابط التحميل:</b>\n{download_url}\n\n"
            "🔑 <b>باسوورد فك الضغط:</b> <code>{password}</code>\n"
            "<i>(اضغط على الباسوورد لنسخه)</i>"
        ),
        "en": (
            "✅ <b>Download Ready!</b>\n\n"
            "📄 <b>File:</b> {file_name}\n"
            "🔢 <b>Version:</b> {version}\n"
            "📦 <b>Size:</b> {size_info}\n\n"
            "🔗 <b>Download Link:</b>\n{download_url}\n\n"
            "🔑 <b>Archive Password:</b> <code>{password}</code>\n"
            "<i>(Tap password to copy)</i>"
        ),
    },
    "no_programs": {
        "ar": "😕 مفيش برامج متاحة حالياً.",
        "en": "😕 No programs available at the moment.",
    },
    "program_not_found": {
        "ar": "⚠️ البرنامج غير موجود.",
        "en": "⚠️ Program not found.",
    },
    "file_not_found": {
        "ar": "⚠️ الملف غير موجود.",
        "en": "⚠️ File not found.",
    },
    "no_files": {
        "ar": "مفيش ملفات مرفوعة للبرنامج ده لسه.",
        "en": "No files uploaded for this program yet.",
    },
    "subscription_required": {
        "ar": (
            "⛔ <b>محتوى للمشتركين فقط!</b>\n\n"
            "عشان تقدر تنزّل ملفات البرامج وتاخد الباسوورد، لازم يكون عندك اشتراك فعّال.\n"
            "اضغط على <b>💳 اشتراك جديد</b> للاشتراك دلوقتي 👇"
        ),
        "en": (
            "⛔ <b>Subscribers Only!</b>\n\n"
            "You need an active subscription to download files and get the password.\n"
            "Tap <b>💳 Subscribe</b> below to get started 👇"
        ),
    },

    # ─── الاشتراكات والدفع ───
    "choose_plan": {
        "ar": "💳 <b>اختار خطة الاشتراك المناسبة ليك:</b>",
        "en": "💳 <b>Choose your subscription plan:</b>",
    },
    "no_plans": {
        "ar": "😕 مفيش خطط اشتراك متاحة حالياً.",
        "en": "😕 No subscription plans available at the moment.",
    },
    "plan_monthly": {
        "ar": "اشتراك شهري",
        "en": "Monthly Plan",
    },
    "plan_yearly": {
        "ar": "اشتراك سنوي",
        "en": "Yearly Plan",
    },
    "choose_payment": {
        "ar": "💰 <b>اختار طريقة الدفع:</b>",
        "en": "💰 <b>Choose a payment method:</b>",
    },
    "no_payment_methods": {
        "ar": "😕 مفيش طرق دفع متاحة حالياً.",
        "en": "😕 No payment methods available.",
    },
    "payment_method_not_found": {
        "ar": "⚠️ طريقة الدفع غير موجودة.",
        "en": "⚠️ Payment method not found.",
    },
    "payment_instructions_template": {
        "ar": (
            "💳 <b>تعليمات الدفع — {method_name}</b>\n\n"
            "💰 <b>المطلوب دفعه:</b> {amount} {currency}\n"
            "📌 <b>بيانات التحويل / اللينك:</b>\n<code>{account_info}</code>\n\n"
            "📝 {instructions}\n\n"
            "📸 <b>ابعت صورة إثبات الدفع (أو رقم العملية) هنا دلوقتي.</b>"
        ),
        "en": (
            "💳 <b>Payment Instructions — {method_name}</b>\n\n"
            "💰 <b>Amount Due:</b> {amount} {currency}\n"
            "📌 <b>Account / Link:</b>\n<code>{account_info}</code>\n\n"
            "📝 {instructions}\n\n"
            "📸 <b>Send your payment proof screenshot (or transaction ID) right here.</b>"
        ),
    },
    "no_plan_selected": {
        "ar": "⚠️ اختار خطة الاشتراك الأول من القائمة.",
        "en": "⚠️ Please select a subscription plan first.",
    },
    "proof_received": {
        "ar": (
            "✅ <b>تم استلام إثبات الدفع بنجاح!</b>\n\n"
            "⏳ الإدارة هتراجع الدفعة وتفعّل اشتراكك في أقرب وقت.\n"
            "هيجيلك إشعار أول ما يتفعل 🎉"
        ),
        "en": (
            "✅ <b>Payment proof received!</b>\n\n"
            "⏳ Our team will review it and activate your subscription shortly.\n"
            "You'll receive a notification once confirmed 🎉"
        ),
    },
    "status_active": {
        "ar": "فعّال ✅",
        "en": "Active ✅",
    },
    "subscription_active_template": {
        "ar": (
            "📊 <b>تفاصيل اشتراكك</b>\n\n"
            "📌 <b>الحالة:</b> {status}\n"
            "📋 <b>الخطة:</b> {plan_type}\n"
            "📅 <b>تاريخ البداية:</b> {start_date}\n"
            "📅 <b>تاريخ الانتهاء:</b> {end_date}"
        ),
        "en": (
            "📊 <b>Your Subscription</b>\n\n"
            "📌 <b>Status:</b> {status}\n"
            "📋 <b>Plan:</b> {plan_type}\n"
            "📅 <b>Start Date:</b> {start_date}\n"
            "📅 <b>End Date:</b> {end_date}"
        ),
    },
    "no_subscription": {
        "ar": "😕 معندكش اشتراك فعّال حالياً.\n\nاشترك دلوقتي عشان تقدر تحمّل كل برامج مرسيدس! 🚗",
        "en": "😕 You don't have an active subscription.\n\nSubscribe now to unlock all Mercedes software downloads! 🚗",
    },
    "payment_confirmed": {
        "ar": (
            "🎉 <b>تم تأكيد الدفع وتفعيل اشتراكك!</b>\n\n"
            "📋 <b>الخطة:</b> {plan_type}\n"
            "📅 <b>ساري حتى:</b> {end_date}\n\n"
            "تقدر دلوقتي تدخل على البرامج وتحمّل الملفات بالباسوورد 🚀"
        ),
        "en": (
            "🎉 <b>Payment Confirmed & Subscription Activated!</b>\n\n"
            "📋 <b>Plan:</b> {plan_type}\n"
            "📅 <b>Valid Until:</b> {end_date}\n\n"
            "You can now browse Programs and download files with passwords 🚀"
        ),
    },
    "payment_confirmed_simple": {
        "ar": "🎉 تم تأكيد دفعتك وتفعيل اشتراكك بنجاح! استمتع بالبرامج 🚀",
        "en": "🎉 Your payment is confirmed and your subscription is now active! 🚀",
    },
    "payment_rejected": {
        "ar": (
            "❌ <b>للأسف تم رفض الدفعة.</b>\n\n"
            "📝 <b>السبب:</b> {reason}\n\n"
            "تقدر تجرب تبعت إثبات تاني أو تتواصل مع الدعم."
        ),
        "en": (
            "❌ <b>Unfortunately, your payment was rejected.</b>\n\n"
            "📝 <b>Reason:</b> {reason}\n\n"
            "Please try again or contact support."
        ),
    },
    "banned_message": {
        "ar": "🚫 حسابك محظور من استخدام البوت. تواصل مع الدعم: {support}",
        "en": "🚫 Your account is banned from using this bot. Contact support: {support}",
    },
}


def get_text(key: str, lang: str = "ar") -> str:
    """بيجيب النص المناسب حسب اللغة من قاموس النصوص"""
    entry = TEXTS.get(key)
    if entry is None:
        return key
    return entry.get(lang, entry.get("ar", key))
