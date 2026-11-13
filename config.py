# config.py
# إعدادات البوت الأساسية - Mercedes Telegram Bot

import os
from typing import Dict, List, Any
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env لو موجود
load_dotenv()

# توكن البوت من BotFather
BOT_TOKEN: str = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

# توكن بوابة الدفع الأوتوماتيك (اختياري - Stripe/Telegram Payments)
PAYMENT_PROVIDER_TOKEN: str = os.getenv("PAYMENT_PROVIDER_TOKEN", "")

# قايمة الأدمنز (أيديهات التليجرام بتاعتهم من .env مفصولة بفاصلة)
_admin_ids_raw = os.getenv("ADMIN_IDS", "123456789")
ADMIN_IDS: List[int] = [
    int(uid.strip())
    for uid in _admin_ids_raw.split(",")
    if uid.strip().isdigit()
]

# مسار قاعدة البيانات
DATABASE_PATH: str = os.getenv("DATABASE_PATH", "mercedes_bot.db")

# خطط الاشتراك المتاحة
SUBSCRIPTION_PLANS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "type": "monthly",
        "price": float(os.getenv("MONTHLY_PRICE", "25")),
        "currency": os.getenv("CURRENCY", "USD"),
        "duration_days": 30,
        "name_ar": "اشتراك شهري (30 يوم)",
        "name_en": "Monthly Plan (30 Days)",
    },
    {
        "id": 2,
        "type": "yearly",
        "price": float(os.getenv("YEARLY_PRICE", "200")),
        "currency": os.getenv("CURRENCY", "USD"),
        "duration_days": 365,
        "name_ar": "اشتراك سنوي (365 يوم)",
        "name_en": "Yearly Plan (365 Days)",
    },
]

# طرق الدفع المتاحة (يدوي + أوتوماتيك)
PAYMENT_METHODS: List[Dict[str, Any]] = [
    {
        "id": 1,
        "key": "vodafone_cash",
        "mode": "manual",
        "name_ar": "📱 فودافون كاش (يدوي)",
        "name_en": "📱 Vodafone Cash (Manual)",
        "account_info": os.getenv("VODAFONE_CASH_NUMBER", "01XXXXXXXXX"),
        "instructions_ar": "حوّل المبلغ على الرقم اللي فوق وابعتلنا سكرين شوت التحويل هنا.",
        "instructions_en": "Transfer the amount to the number above and send the screenshot here.",
    },
    {
        "id": 2,
        "key": "instapay",
        "mode": "manual",
        "name_ar": "⚡ إنستاباي (يدوي)",
        "name_en": "⚡ InstaPay (Manual)",
        "account_info": os.getenv("INSTAPAY_ADDRESS", "username@instapay"),
        "instructions_ar": "حوّل المبلغ على عنوان إنستاباي اللي فوق وابعتلنا سكرين شوت التحويل هنا.",
        "instructions_en": "Transfer the amount to the InstaPay address above and send the screenshot here.",
    },
    {
        "id": 3,
        "key": "bank_transfer",
        "mode": "manual",
        "name_ar": "🏦 تحويل بنكي (يدوي)",
        "name_en": "🏦 Bank Transfer (Manual)",
        "account_info": os.getenv("BANK_ACCOUNT", "IBAN / Account: XXXXXXXXXXXX"),
        "instructions_ar": "حوّل المبلغ على الحساب البنكي وابعتلنا صورة الإيصال هنا.",
        "instructions_en": "Transfer to the bank account above and send the receipt photo here.",
    },
    {
        "id": 4,
        "key": "paypal",
        "mode": "online",
        "name_ar": "💳 PayPal / كارت بنكي (أونلاين)",
        "name_en": "💳 PayPal / Card (Online)",
        "account_info": os.getenv("PAYPAL_LINK", "https://paypal.me/yourusername"),
        "instructions_ar": "ادفع من اللينك اللي فوق وبعدين ابعتلنا سكرين شوت أو رقم العملية للتأكيد.",
        "instructions_en": "Pay via the link above, then send a screenshot or transaction ID to confirm.",
    },
    {
        "id": 5,
        "key": "crypto",
        "mode": "online",
        "name_ar": "🪙 USDT / كريبتو",
        "name_en": "🪙 USDT / Crypto",
        "account_info": os.getenv("USDT_ADDRESS", "TRC20: TXXXXXXXXXXXXXXXXXXXXXXXX"),
        "instructions_ar": "ابعت المبلغ على محفظة USDT (TRC20) وبعدين ابعت سكرين شوت التحويل هنا.",
        "instructions_en": "Send USDT (TRC20) to the address above, then send a screenshot here.",
    },
]

# اللغة الافتراضية
DEFAULT_LANGUAGE: str = "ar"

# يوزرنيم الدعم الفني
SUPPORT_USERNAME: str = os.getenv("SUPPORT_USERNAME", "@your_support_username")
