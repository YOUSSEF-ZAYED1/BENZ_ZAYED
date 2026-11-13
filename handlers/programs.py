"""
handlers/programs.py
هاندلرز تصفح البرامج وتحميل الملفات
"""

import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, CallbackQueryHandler

from config import SUPPORT_USERNAME
from database import (
    get_user,
    get_active_programs,
    get_program_by_id,
    get_program_files,
    get_file_by_id,
    get_active_subscription,
    log_download,
)
from utils.texts import get_text


# ──────────────────────────── قائمة البرامج ────────────────────────────

async def programs_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض قائمة البرامج النشطة كأزرار إنلاين"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    if db_user and db_user.get("is_banned"):
        await query.edit_message_text(
            get_text("banned_message", lang).format(support=SUPPORT_USERNAME),
            parse_mode="HTML",
        )
        return

    programs = await get_active_programs()

    if not programs:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                get_text("btn_back_menu", lang),
                callback_data="back_menu",
            )]
        ])
        await query.edit_message_text(
            get_text("no_programs", lang),
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    # بناء كيبورد البرامج – كل برنامج في صف لوحده
    buttons = []
    for prog in programs:
        name = prog.get(f"name_{lang}", prog.get("name_en", "—"))
        buttons.append([
            InlineKeyboardButton(
                f"📂 {name}",
                callback_data=f"prog_detail_{prog['id']}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            get_text("btn_back_menu", lang),
            callback_data="back_menu",
        )
    ])

    await query.edit_message_text(
        get_text("programs_title", lang),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )


# ──────────────────────────── تفاصيل برنامج ────────────────────────────

async def program_detail(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض تفاصيل برنامج معين مع أزرار الملفات"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    program_id = int(query.data.split("_")[-1])
    program = await get_program_by_id(program_id)

    if not program:
        await query.edit_message_text(get_text("program_not_found", lang))
        return

    name = html.escape(program.get(f"name_{lang}") or program.get("name_en") or "—")
    desc = html.escape(program.get(f"description_{lang}") or program.get("description_en") or "—")
    version = html.escape(program.get("version") or "—")
    category = html.escape(program.get("category") or "—")

    text = get_text("program_detail_template", lang).format(
        name=name,
        description=desc,
        version=version,
        category=category,
    )

    files = await get_program_files(program_id)
    buttons = []

    if files:
        for f in files:
            file_label = f.get("file_name", "File")
            f_ver = f.get("version", "")
            size_info = f.get("size_info", "")
            label = f"📥 {file_label}"
            if f_ver:
                label += f" v{f_ver}"
            if size_info:
                label += f" ({size_info})"
            buttons.append([
                InlineKeyboardButton(label, callback_data=f"prog_file_{f['id']}")
            ])
    else:
        text += f"\n\n⚠️ {get_text('no_files', lang)}"

    buttons.append([
        InlineKeyboardButton(
            get_text("btn_back_programs", lang),
            callback_data="prog_menu",
        )
    ])

    await query.edit_message_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )


# ──────────────────────────── تحميل ملف ────────────────────────────

async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تحميل ملف – التحقق من الاشتراك الأول وإرسال الرابط والباسوورد"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    if db_user and db_user.get("is_banned"):
        await query.edit_message_text(
            get_text("banned_message", lang).format(support=SUPPORT_USERNAME),
            parse_mode="HTML",
        )
        return

    file_id = int(query.data.split("_")[-1])
    file_info = await get_file_by_id(file_id)

    if not file_info:
        await query.edit_message_text(get_text("file_not_found", lang))
        return

    # التحقق من وجود اشتراك نشط
    subscription = await get_active_subscription(user_id)

    if not subscription:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                get_text("btn_subscribe", lang),
                callback_data="sub_menu",
            )],
            [InlineKeyboardButton(
                get_text("btn_back_programs", lang),
                callback_data="prog_menu",
            )],
        ])
        await query.edit_message_text(
            get_text("subscription_required", lang),
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    # المستخدم مشترك → إرسال رابط التحميل وباسوورد النسخة
    download_url = html.escape(file_info.get("download_url") or "—")
    password = html.escape(file_info.get("password") or "—")
    file_name = html.escape(file_info.get("file_name") or "—")
    version = html.escape(file_info.get("version") or "—")
    size_info = html.escape(file_info.get("size_info") or "N/A")

    text = get_text("download_info_template", lang).format(
        file_name=file_name,
        version=version,
        size_info=size_info,
        download_url=download_url,
        password=password,
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            get_text("btn_back_programs", lang),
            callback_data="prog_menu",
        )],
    ])

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )

    # تسجيل التحميل في قاعدة البيانات
    await log_download(user_id=user_id, file_id=file_id)


# ──────────────────────────── تسجيل الهاندلرز ────────────────────────────

def register_program_handlers(app) -> None:
    """تسجيل كل هاندلرز البرامج في الأبليكيشن"""
    app.add_handler(CallbackQueryHandler(programs_menu, pattern=r"^prog_menu$"))
    app.add_handler(CallbackQueryHandler(program_detail, pattern=r"^prog_detail_\d+$"))
    app.add_handler(CallbackQueryHandler(download_file, pattern=r"^prog_file_\d+$"))
