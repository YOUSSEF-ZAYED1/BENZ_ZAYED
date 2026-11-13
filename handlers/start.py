"""
handlers/start.py
هاندلرز البداية واختيار اللغة والقائمة الرئيسية
"""

import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
)

from database import get_user, create_user, update_user_language
from config import SUPPORT_USERNAME
from utils.texts import get_text
from utils.helpers import build_main_menu_keyboard


# ──────────────────────────── /start ────────────────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر /start – تسجيل المستخدم الجديد وعرض اختيار اللغة"""
    user = update.effective_user
    db_user = await get_user(user.id)

    if db_user is None:
        # مستخدم جديد → نسجله في قاعدة البيانات
        await create_user(
            user_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name,
        )
    elif db_user.get("is_banned"):
        lang = db_user.get("lang", "ar")
        await update.message.reply_text(
            get_text("banned_message", lang).format(support=SUPPORT_USERNAME),
            parse_mode="HTML",
        )
        return

    # إزالة أي كيبورد قديم (ReplyKeyboard) كان متعلق في الشات من البوت القديم
    await update.message.reply_text(
        "🚗 أهلاً بيك في بوت برامج مرسيدس!",
        reply_markup=ReplyKeyboardRemove(),
    )

    # كيبورد اختيار اللغة
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇪🇬 العربية", callback_data="lang_ar"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ])

    await update.message.reply_text(
        "🌐 اختر اللغة / Choose your language:",
        reply_markup=keyboard,
    )


# ──────────────────────────── اختيار اللغة ────────────────────────────

async def language_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هاندلر كولباك اختيار اللغة (ar / en)"""
    query = update.callback_query
    await query.answer()

    lang = query.data.split("_")[1]  # lang_ar → ar  /  lang_en → en
    user_id = query.from_user.id

    # التأكد إن المستخدم متسجل قبل تحديث اللغة
    db_user = await get_user(user_id)
    if db_user is None:
        await create_user(
            user_id=user_id,
            username=query.from_user.username,
            first_name=query.from_user.first_name,
            last_name=query.from_user.last_name,
            lang=lang,
        )
    else:
        await update_user_language(user_id, lang)

    context.user_data["lang"] = lang

    safe_name = html.escape(query.from_user.first_name or "")
    welcome = get_text("welcome", lang).format(name=safe_name)
    keyboard = build_main_menu_keyboard(lang)

    await query.edit_message_text(
        text=welcome,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def menu_lang_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تغيير اللغة من القائمة الرئيسية"""
    query = update.callback_query
    await query.answer()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🇪🇬 العربية", callback_data="lang_ar"),
            InlineKeyboardButton("🇬🇧 English", callback_data="lang_en"),
        ]
    ])
    await query.edit_message_text(
        "🌐 اختر اللغة / Choose your language:",
        reply_markup=keyboard,
    )


# ──────────────────────────── القائمة الرئيسية ────────────────────────────

async def back_to_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رجوع للقائمة الرئيسية من أي شاشة"""
    query = update.callback_query
    await query.answer()

    # لو كان المستخدم في وضع انتظار إثبات الدفع نلغيه
    context.user_data["awaiting_proof"] = False

    user_id = query.from_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"
    context.user_data["lang"] = lang

    text = get_text("main_menu", lang)
    keyboard = build_main_menu_keyboard(lang)

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ──────────────────────────── المساعدة وعن البوت ────────────────────────────

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر /help – عرض رسالة المساعدة"""
    user_id = update.effective_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    support_link = f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("btn_contact_support", lang), url=support_link)],
        [InlineKeyboardButton(get_text("btn_back_menu", lang), callback_data="back_menu")],
    ])

    await update.message.reply_text(
        get_text("help_message", lang).format(support=SUPPORT_USERNAME),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def menu_help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض المساعدة من زر القائمة الرئيسية"""
    query = update.callback_query
    await query.answer()

    db_user = await get_user(query.from_user.id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    support_link = f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("btn_contact_support", lang), url=support_link)],
        [InlineKeyboardButton(get_text("btn_back_menu", lang), callback_data="back_menu")],
    ])
    await query.edit_message_text(
        get_text("help_message", lang).format(support=SUPPORT_USERNAME),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر /about – معلومات عن البوت"""
    user_id = update.effective_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    support_link = f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("btn_contact_support", lang), url=support_link)],
        [InlineKeyboardButton(get_text("btn_back_menu", lang), callback_data="back_menu")],
    ])

    await update.message.reply_text(
        get_text("about_message", lang).format(support=SUPPORT_USERNAME),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


async def menu_about_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض معلومات البوت من زر القائمة الرئيسية"""
    query = update.callback_query
    await query.answer()

    db_user = await get_user(query.from_user.id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    support_link = f"https://t.me/{SUPPORT_USERNAME.lstrip('@')}"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("btn_contact_support", lang), url=support_link)],
        [InlineKeyboardButton(get_text("btn_back_menu", lang), callback_data="back_menu")],
    ])
    await query.edit_message_text(
        get_text("about_message", lang).format(support=SUPPORT_USERNAME),
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ──────────────────────────── تسجيل الهاندلرز ────────────────────────────

def register_start_handlers(app) -> None:
    """تسجيل كل هاندلرز البداية في الأبليكيشن"""
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(CallbackQueryHandler(language_callback, pattern=r"^lang_(ar|en)$"))
    app.add_handler(CallbackQueryHandler(menu_lang_callback, pattern=r"^menu_lang$"))
    app.add_handler(CallbackQueryHandler(menu_help_callback, pattern=r"^menu_help$"))
    app.add_handler(CallbackQueryHandler(menu_about_callback, pattern=r"^menu_about$"))
    app.add_handler(CallbackQueryHandler(back_to_menu, pattern=r"^back_menu$"))
