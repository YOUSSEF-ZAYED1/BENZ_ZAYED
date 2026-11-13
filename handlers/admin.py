"""
handlers/admin.py
هاندلرز لوحة تحكم الأدمن – إحصائيات، مدفوعات، برامج، إذاعة، إلخ
"""

import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from database import (
    get_user,
    get_all_users,
    get_users_paginated,
    get_stats,
    get_pending_payments,
    get_payment_by_id,
    confirm_payment_record,
    reject_payment_record,
    create_program,
    get_active_programs,
    get_program_by_id,
    get_program_files,
    create_file_record,
    get_file_by_id,
    update_file_password,
    ban_user,
    unban_user,
)
from config import ADMIN_IDS
from utils.texts import get_text
from utils.helpers import format_date, is_admin

logger = logging.getLogger(__name__)

# ─── حالات المحادثة (ConversationHandler states) ───
# إضافة برنامج
(
    ADD_PROG_NAME_EN,
    ADD_PROG_NAME_AR,
    ADD_PROG_DESC_EN,
    ADD_PROG_DESC_AR,
    ADD_PROG_CATEGORY,
    ADD_PROG_VERSION,
    ADD_PROG_CONFIRM,
) = range(7)

# إضافة ملف
(
    ADD_FILE_SELECT_PROG,
    ADD_FILE_NAME,
    ADD_FILE_URL,
    ADD_FILE_PASSWORD,
    ADD_FILE_VERSION,
    ADD_FILE_SIZE,
    ADD_FILE_CONFIRM,
) = range(10, 17)

# تحديث باسوورد
(
    UPD_PASS_SELECT_PROG,
    UPD_PASS_SELECT_FILE,
    UPD_PASS_ENTER,
    UPD_PASS_CONFIRM,
) = range(20, 24)

# إذاعة
BROADCAST_MSG, BROADCAST_CONFIRM = range(30, 32)

# رفض دفعة (سبب الرفض)
REJECT_REASON = 40

# عدد المستخدمين في كل صفحة
USERS_PER_PAGE = 10


# ──────────────────── ديكوريتور فحص الأدمن ────────────────────

def admin_required(func):
    """ديكوريتور يتحقق إن المستخدم أدمن قبل تنفيذ أي عملية"""
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        if not is_admin(user_id):
            if update.callback_query:
                await update.callback_query.answer(
                    "⛔ غير مصرح / Unauthorized", show_alert=True
                )
            else:
                await update.effective_message.reply_text("⛔ غير مصرح / Unauthorized")
            return ConversationHandler.END
        return await func(update, context, *args, **kwargs)
    return wrapper


# ════════════════════════════════════════════════════════════════
#  القائمة الرئيسية للأدمن
# ════════════════════════════════════════════════════════════════

@admin_required
async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """أمر /admin – عرض لوحة تحكم الأدمن"""
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📊 إحصائيات / Stats", callback_data="admin_stats"),
            InlineKeyboardButton("⏳ معلقة / Pending", callback_data="admin_pending"),
        ],
        [
            InlineKeyboardButton("➕ إضافة برنامج / Add Program", callback_data="admin_add_prog"),
            InlineKeyboardButton("📎 إضافة ملف / Add File", callback_data="admin_add_file"),
        ],
        [
            InlineKeyboardButton("🔄 تحديث باسوورد / Update Pass", callback_data="admin_upd_pass"),
            InlineKeyboardButton("📢 إذاعة / Broadcast", callback_data="admin_broadcast"),
        ],
        [
            InlineKeyboardButton("👥 المستخدمين / Users", callback_data="admin_users_0"),
        ],
    ])

    text = "🛠 <b>لوحة التحكم / Admin Panel</b>"

    if update.message:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.callback_query.edit_message_text(
            text, reply_markup=keyboard, parse_mode="HTML"
        )


@admin_required
async def admin_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """رجوع لقائمة الأدمن من كولباك"""
    query = update.callback_query
    await query.answer()
    # إعادة استخدام نفس دالة القائمة
    await admin_command(update, context)


# ════════════════════════════════════════════════════════════════
#  الإحصائيات
# ════════════════════════════════════════════════════════════════

@admin_required
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض إحصائيات البوت"""
    query = update.callback_query
    await query.answer()

    stats = await get_stats()

    text = (
        "📊 <b>إحصائيات البوت / Bot Statistics</b>\n\n"
        f"👥 المستخدمين / Users: <b>{stats.get('total_users', 0)}</b>\n"
        f"✅ اشتراكات نشطة / Active Subs: <b>{stats.get('active_subscriptions', 0)}</b>\n"
        f"⏳ مدفوعات معلقة / Pending: <b>{stats.get('pending_payments', 0)}</b>\n"
        f"📥 إجمالي التحميلات / Downloads: <b>{stats.get('total_downloads', 0)}</b>\n"
        f"💰 إجمالي الإيرادات / Revenue: <b>{stats.get('total_revenue', 0)}</b>"
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع / Back", callback_data="admin_panel")]
    ])

    await query.edit_message_text(text, reply_markup=keyboard, parse_mode="HTML")


# ════════════════════════════════════════════════════════════════
#  المدفوعات المعلقة
# ════════════════════════════════════════════════════════════════

@admin_required
async def pending_payments(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض قائمة المدفوعات المعلقة"""
    query = update.callback_query
    await query.answer()

    payments = await get_pending_payments()

    if not payments:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع / Back", callback_data="admin_panel")]
        ])
        await query.edit_message_text(
            "✅ لا يوجد مدفوعات معلقة / No pending payments",
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    # عرض كل دفعة مع أزرار التأكيد والرفض
    await query.edit_message_text(
        f"⏳ <b>مدفوعات معلقة / Pending Payments ({len(payments)})</b>",
        parse_mode="HTML",
    )

    for pay in payments:
        user_info = await get_user(pay["user_id"])
        username = user_info.get("username", "—") if user_info else "—"
        first_name = user_info.get("first_name", "—") if user_info else "—"

        caption = (
            f"🧾 <b>Payment #{pay['id']}</b>\n"
            f"👤 {first_name} (@{username})\n"
            f"🆔 ID: <code>{pay['user_id']}</code>\n"
            f"📅 {format_date(pay.get('created_at'))}\n"
            f"💰 {pay.get('amount', '—')} {pay.get('currency', '')}"
        )

        admin_keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "✅ تأكيد / Confirm",
                    callback_data=f"admin_confirm_{pay['id']}",
                ),
                InlineKeyboardButton(
                    "❌ رفض / Reject",
                    callback_data=f"admin_reject_{pay['id']}",
                ),
            ]
        ])

        try:
            if pay.get("proof_file_id"):
                await context.bot.send_photo(
                    chat_id=query.from_user.id,
                    photo=pay["proof_file_id"],
                    caption=caption,
                    reply_markup=admin_keyboard,
                    parse_mode="HTML",
                )
            else:
                await context.bot.send_message(
                    chat_id=query.from_user.id,
                    text=caption,
                    reply_markup=admin_keyboard,
                    parse_mode="HTML",
                )
        except Exception as e:
            logger.error("خطأ في عرض دفعة معلقة: %s", e)


# ──────────────────── تأكيد دفعة ────────────────────

@admin_required
async def confirm_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تأكيد دفعة وتفعيل الاشتراك"""
    query = update.callback_query
    await query.answer("✅ تم التأكيد / Confirmed")

    payment_id = int(query.data.split("_")[-1])
    payment = await get_payment_by_id(payment_id)

    if not payment:
        await query.edit_message_caption(caption="⚠️ الدفعة غير موجودة / Payment not found")
        return

    # تفعيل الاشتراك وتحديث حالة الدفع
    subscription = await confirm_payment_record(payment_id, admin_id=query.from_user.id)

    # تحديث رسالة الأدمن (سواء كانت صورة بكابشن أو رسالة نصية)
    confirm_footer = (
        f"\n\n✅ <b>تم التأكيد / Confirmed</b> بواسطة "
        f"{query.from_user.first_name}"
    )
    if query.message.photo:
        await query.edit_message_caption(
            caption=f"{query.message.caption or ''}{confirm_footer}",
            parse_mode="HTML",
        )
    else:
        await query.edit_message_text(
            text=f"{query.message.text or ''}{confirm_footer}",
            parse_mode="HTML",
        )

    # إشعار المستخدم
    user_id = payment["user_id"]
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    if subscription:
        end_date = format_date(subscription.get("end_date"))
        plan_type = get_text(f"plan_{subscription.get('plan_type', 'monthly')}", lang)
        text = get_text("payment_confirmed", lang).format(
            plan_type=plan_type,
            end_date=end_date,
        )
    else:
        text = get_text("payment_confirmed_simple", lang)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            get_text("btn_back_menu", lang),
            callback_data="back_menu",
        )]
    ])

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("فشل إرسال إشعار تأكيد للمستخدم %s: %s", user_id, e)


# ──────────────────── رفض دفعة (مع سبب) ────────────────────

@admin_required
async def reject_payment_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية رفض دفعة – طلب سبب الرفض من الأدمن"""
    query = update.callback_query
    await query.answer()

    payment_id = int(query.data.split("_")[-1])
    context.user_data["rejecting_payment_id"] = payment_id

    await query.message.reply_text(
        "📝 اكتب سبب الرفض / Enter rejection reason:",
        parse_mode="HTML",
    )
    return REJECT_REASON


@admin_required
async def reject_payment_reason(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام سبب الرفض وتنفيذ الرفض"""
    reason = update.message.text
    payment_id = context.user_data.get("rejecting_payment_id")

    if not payment_id:
        await update.message.reply_text("⚠️ خطأ / Error")
        return ConversationHandler.END

    payment = await get_payment_by_id(payment_id)

    if not payment:
        await update.message.reply_text("⚠️ الدفعة غير موجودة / Payment not found")
        return ConversationHandler.END

    # رفض الدفعة في قاعدة البيانات
    await reject_payment_record(payment_id, reason=reason, admin_id=update.effective_user.id)

    await update.message.reply_text(
        f"❌ تم رفض الدفعة #{payment_id} / Payment rejected",
        parse_mode="HTML",
    )

    # إشعار المستخدم بالرفض
    user_id = payment["user_id"]
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    text = get_text("payment_rejected", lang).format(reason=reason)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            get_text("btn_subscribe", lang),
            callback_data="sub_menu",
        )],
        [InlineKeyboardButton(
            get_text("btn_back_menu", lang),
            callback_data="back_menu",
        )],
    ])

    try:
        await context.bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("فشل إرسال إشعار رفض للمستخدم %s: %s", user_id, e)

    context.user_data.pop("rejecting_payment_id", None)
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════
#  إضافة برنامج (ConversationHandler)
# ════════════════════════════════════════════════════════════════

@admin_required
async def add_program_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية إضافة برنامج → طلب الاسم بالإنجليزي"""
    query = update.callback_query
    await query.answer()

    context.user_data["new_program"] = {}
    await query.edit_message_text(
        "📝 <b>إضافة برنامج جديد / Add New Program</b>\n\n"
        "1/6 — أدخل اسم البرنامج بالإنجليزي / Enter program name in English:",
        parse_mode="HTML",
    )
    return ADD_PROG_NAME_EN


async def add_prog_name_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الاسم بالإنجليزي → طلب الاسم بالعربي"""
    context.user_data["new_program"]["name_en"] = update.message.text
    await update.message.reply_text(
        "2/6 — أدخل اسم البرنامج بالعربي / Enter program name in Arabic:"
    )
    return ADD_PROG_NAME_AR


async def add_prog_name_ar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الاسم بالعربي → طلب الوصف بالإنجليزي"""
    context.user_data["new_program"]["name_ar"] = update.message.text
    await update.message.reply_text(
        "3/6 — أدخل الوصف بالإنجليزي / Enter description in English:"
    )
    return ADD_PROG_DESC_EN


async def add_prog_desc_en(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الوصف بالإنجليزي → طلب الوصف بالعربي"""
    context.user_data["new_program"]["description_en"] = update.message.text
    await update.message.reply_text(
        "4/6 — أدخل الوصف بالعربي / Enter description in Arabic:"
    )
    return ADD_PROG_DESC_AR


async def add_prog_desc_ar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الوصف بالعربي → طلب الفئة"""
    context.user_data["new_program"]["description_ar"] = update.message.text
    await update.message.reply_text(
        "5/6 — أدخل فئة البرنامج / Enter category (e.g., DAS, Xentry, WIS):"
    )
    return ADD_PROG_CATEGORY


async def add_prog_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الفئة → طلب الإصدار"""
    context.user_data["new_program"]["category"] = update.message.text
    await update.message.reply_text("6/6 — أدخل رقم الإصدار / Enter version:")
    return ADD_PROG_VERSION


async def add_prog_version(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الإصدار → عرض ملخص للتأكيد"""
    context.user_data["new_program"]["version"] = update.message.text
    prog = context.user_data["new_program"]

    summary = (
        "📋 <b>ملخص البرنامج / Program Summary</b>\n\n"
        f"🔤 EN: {prog['name_en']}\n"
        f"🔤 AR: {prog['name_ar']}\n"
        f"📝 Desc EN: {prog['description_en']}\n"
        f"📝 Desc AR: {prog['description_ar']}\n"
        f"📁 Category: {prog['category']}\n"
        f"🏷 Version: {prog['version']}\n\n"
        "هل تريد الحفظ؟ / Save?"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ حفظ / Save", callback_data="admin_prog_save"),
            InlineKeyboardButton("❌ إلغاء / Cancel", callback_data="admin_prog_cancel"),
        ]
    ])

    await update.message.reply_text(summary, reply_markup=keyboard, parse_mode="HTML")
    return ADD_PROG_CONFIRM


async def add_prog_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تأكيد حفظ البرنامج أو إلغاء"""
    query = update.callback_query
    await query.answer()

    if query.data == "admin_prog_save":
        prog = context.user_data.get("new_program", {})
        await create_program(**prog)
        await query.edit_message_text("✅ تم حفظ البرنامج بنجاح / Program saved!")
    else:
        await query.edit_message_text("❌ تم الإلغاء / Cancelled")

    context.user_data.pop("new_program", None)
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════
#  إضافة ملف لبرنامج (ConversationHandler)
# ════════════════════════════════════════════════════════════════

@admin_required
async def add_file_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية إضافة ملف → عرض قائمة البرامج للاختيار"""
    query = update.callback_query
    await query.answer()

    programs = await get_active_programs()
    if not programs:
        await query.edit_message_text("⚠️ لا يوجد برامج / No programs found")
        return ConversationHandler.END

    buttons = []
    for prog in programs:
        buttons.append([
            InlineKeyboardButton(
                prog.get("name_en", "—"),
                callback_data=f"admin_filefor_{prog['id']}",
            )
        ])
    buttons.append([
        InlineKeyboardButton("❌ إلغاء / Cancel", callback_data="admin_file_cancel")
    ])

    context.user_data["new_file"] = {}
    await query.edit_message_text(
        "📎 <b>إضافة ملف / Add File</b>\n\n"
        "اختر البرنامج / Select program:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )
    return ADD_FILE_SELECT_PROG


async def add_file_select_prog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """اختيار البرنامج → طلب اسم الملف"""
    query = update.callback_query
    await query.answer()

    if query.data == "admin_file_cancel":
        await query.edit_message_text("❌ تم الإلغاء / Cancelled")
        context.user_data.pop("new_file", None)
        return ConversationHandler.END

    prog_id = int(query.data.split("_")[-1])
    context.user_data["new_file"]["program_id"] = prog_id

    await query.edit_message_text("1/5 — أدخل اسم الملف / Enter file name:")
    return ADD_FILE_NAME


async def add_file_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام اسم الملف → طلب رابط التحميل"""
    context.user_data["new_file"]["file_name"] = update.message.text
    await update.message.reply_text("2/5 — أدخل رابط التحميل / Enter download URL:")
    return ADD_FILE_URL


async def add_file_url(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الرابط → طلب الباسوورد"""
    context.user_data["new_file"]["download_url"] = update.message.text
    await update.message.reply_text("3/5 — أدخل كلمة المرور / Enter password:")
    return ADD_FILE_PASSWORD


async def add_file_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الباسوورد → طلب الإصدار"""
    context.user_data["new_file"]["password"] = update.message.text
    await update.message.reply_text("4/5 — أدخل رقم الإصدار / Enter version:")
    return ADD_FILE_VERSION


async def add_file_version(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الإصدار → طلب حجم الملف"""
    context.user_data["new_file"]["version"] = update.message.text
    await update.message.reply_text(
        "5/5 — أدخل حجم الملف / Enter size info (e.g., 2.5 GB):"
    )
    return ADD_FILE_SIZE


async def add_file_size(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الحجم → عرض ملخص للتأكيد"""
    context.user_data["new_file"]["size_info"] = update.message.text
    f = context.user_data["new_file"]

    summary = (
        "📋 <b>ملخص الملف / File Summary</b>\n\n"
        f"📁 Program ID: {f['program_id']}\n"
        f"📄 Name: {f['file_name']}\n"
        f"🔗 URL: {f['download_url']}\n"
        f"🔑 Password: <tg-spoiler>{f['password']}</tg-spoiler>\n"
        f"🏷 Version: {f['version']}\n"
        f"📦 Size: {f['size_info']}\n\n"
        "هل تريد الحفظ؟ / Save?"
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ حفظ / Save", callback_data="admin_file_save"),
            InlineKeyboardButton("❌ إلغاء / Cancel", callback_data="admin_file_cancel"),
        ]
    ])

    await update.message.reply_text(summary, reply_markup=keyboard, parse_mode="HTML")
    return ADD_FILE_CONFIRM


async def add_file_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تأكيد حفظ الملف أو إلغاء"""
    query = update.callback_query
    await query.answer()

    if query.data == "admin_file_save":
        f = context.user_data.get("new_file", {})
        await create_file_record(**f)
        await query.edit_message_text("✅ تم حفظ الملف بنجاح / File saved!")
    else:
        await query.edit_message_text("❌ تم الإلغاء / Cancelled")

    context.user_data.pop("new_file", None)
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════
#  تحديث باسوورد ملف (ConversationHandler)
# ════════════════════════════════════════════════════════════════

@admin_required
async def update_password_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية تحديث باسوورد → اختيار البرنامج"""
    query = update.callback_query
    await query.answer()

    programs = await get_active_programs()
    if not programs:
        await query.edit_message_text("⚠️ لا يوجد برامج / No programs found")
        return ConversationHandler.END

    buttons = []
    for prog in programs:
        buttons.append([
            InlineKeyboardButton(
                prog.get("name_en", "—"),
                callback_data=f"admin_updp_{prog['id']}",
            )
        ])
    buttons.append([
        InlineKeyboardButton("❌ إلغاء / Cancel", callback_data="admin_updp_cancel")
    ])

    await query.edit_message_text(
        "🔄 <b>تحديث باسوورد / Update Password</b>\n\n"
        "اختر البرنامج / Select program:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )
    return UPD_PASS_SELECT_PROG


async def upd_pass_select_prog(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """اختيار البرنامج → عرض ملفاته"""
    query = update.callback_query
    await query.answer()

    if query.data == "admin_updp_cancel":
        await query.edit_message_text("❌ تم الإلغاء / Cancelled")
        return ConversationHandler.END

    prog_id = int(query.data.split("_")[-1])
    files = await get_program_files(prog_id)

    if not files:
        await query.edit_message_text("⚠️ لا يوجد ملفات / No files found")
        return ConversationHandler.END

    buttons = []
    for f in files:
        buttons.append([
            InlineKeyboardButton(
                f.get("file_name", "—"),
                callback_data=f"admin_updpf_{f['id']}",
            )
        ])
    buttons.append([
        InlineKeyboardButton("❌ إلغاء / Cancel", callback_data="admin_updpf_cancel2")
    ])

    await query.edit_message_text(
        "📄 اختر الملف / Select file:",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )
    return UPD_PASS_SELECT_FILE


async def upd_pass_select_file(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """اختيار الملف → طلب الباسوورد الجديد"""
    query = update.callback_query
    await query.answer()

    if query.data == "admin_updp_cancel2":
        await query.edit_message_text("❌ تم الإلغاء / Cancelled")
        return ConversationHandler.END

    file_id = int(query.data.split("_")[-1])
    context.user_data["upd_pass_file_id"] = file_id

    await query.edit_message_text("🔑 أدخل كلمة المرور الجديدة / Enter new password:")
    return UPD_PASS_ENTER


async def upd_pass_enter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام الباسوورد الجديد → تأكيد"""
    new_password = update.message.text
    context.user_data["new_password"] = new_password

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأكيد / Confirm", callback_data="admin_updp_confirm"),
            InlineKeyboardButton("❌ إلغاء / Cancel", callback_data="admin_updp_cancel3"),
        ]
    ])

    await update.message.reply_text(
        f"🔑 كلمة المرور الجديدة: <tg-spoiler>{new_password}</tg-spoiler>\n\n"
        "تأكيد؟ / Confirm?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return UPD_PASS_CONFIRM


async def upd_pass_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تأكيد تحديث الباسوورد"""
    query = update.callback_query
    await query.answer()

    if query.data == "admin_updp_confirm":
        file_id = context.user_data.get("upd_pass_file_id")
        new_password = context.user_data.get("new_password")
        await update_file_password(file_id, new_password)
        await query.edit_message_text("✅ تم تحديث كلمة المرور / Password updated!")
    else:
        await query.edit_message_text("❌ تم الإلغاء / Cancelled")

    context.user_data.pop("upd_pass_file_id", None)
    context.user_data.pop("new_password", None)
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════
#  الإذاعة (ConversationHandler)
# ════════════════════════════════════════════════════════════════

@admin_required
async def broadcast_start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """بداية الإذاعة → طلب الرسالة"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📢 <b>إذاعة / Broadcast</b>\n\n"
        "أرسل الرسالة اللي عايز توصلها لكل المستخدمين:\n"
        "Send the message to broadcast to all users:\n\n"
        "أرسل /cancel للإلغاء",
        parse_mode="HTML",
    )
    return BROADCAST_MSG


async def broadcast_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """استلام رسالة الإذاعة → تأكيد"""
    context.user_data["broadcast_text"] = update.message.text

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ إرسال / Send", callback_data="admin_bc_send"),
            InlineKeyboardButton("❌ إلغاء / Cancel", callback_data="admin_bc_cancel"),
        ]
    ])

    await update.message.reply_text(
        f"📢 <b>معاينة الإذاعة / Preview</b>\n\n"
        f"{update.message.text}\n\n"
        f"إرسال لجميع المستخدمين؟ / Send to all users?",
        reply_markup=keyboard,
        parse_mode="HTML",
    )
    return BROADCAST_CONFIRM


async def broadcast_confirm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """تأكيد إرسال الإذاعة أو إلغاء"""
    query = update.callback_query
    await query.answer()

    if query.data == "admin_bc_cancel":
        await query.edit_message_text("❌ تم إلغاء الإذاعة / Broadcast cancelled")
        context.user_data.pop("broadcast_text", None)
        return ConversationHandler.END

    broadcast_text = context.user_data.get("broadcast_text", "")
    users = await get_all_users()

    sent = 0
    failed = 0

    await query.edit_message_text("📤 جاري الإرسال... / Sending...")

    for user in users:
        # تخطي المستخدمين المحظورين
        if user.get("is_banned"):
            continue
        try:
            await context.bot.send_message(
                chat_id=user["user_id"],
                text=broadcast_text,
                parse_mode="HTML",
            )
            sent += 1
        except Exception:
            # المستخدم بلوك البوت أو مشكلة تانية
            failed += 1

    await context.bot.send_message(
        chat_id=query.from_user.id,
        text=(
            f"📢 <b>نتيجة الإذاعة / Broadcast Result</b>\n\n"
            f"✅ تم الإرسال / Sent: {sent}\n"
            f"❌ فشل / Failed: {failed}"
        ),
        parse_mode="HTML",
    )

    context.user_data.pop("broadcast_text", None)
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════
#  قائمة المستخدمين (paginated)
# ════════════════════════════════════════════════════════════════

@admin_required
async def user_list(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض قائمة المستخدمين مع أزرار حظر/إلغاء حظر"""
    query = update.callback_query
    await query.answer()

    # استخراج رقم الصفحة من الكولباك
    page = int(query.data.split("_")[-1])

    result = await get_users_paginated(page=page, per_page=USERS_PER_PAGE)
    users = result.get("users", [])
    total = result.get("total", 0)
    total_pages = max(1, (total + USERS_PER_PAGE - 1) // USERS_PER_PAGE)

    if not users:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع / Back", callback_data="admin_panel")]
        ])
        await query.edit_message_text(
            "👥 لا يوجد مستخدمين / No users",
            reply_markup=keyboard,
        )
        return

    # بناء نص القائمة
    lines = [f"👥 <b>المستخدمين / Users ({total})</b>\n"]
    buttons = []

    for u in users:
        status = "🚫" if u.get("is_banned") else "✅"
        name = u.get("first_name", "—")
        username = f"@{u.get('username')}" if u.get("username") else ""
        lines.append(f"{status} {name} {username} — <code>{u['user_id']}</code>")

        # زرار حظر/إلغاء حظر
        if u.get("is_banned"):
            buttons.append([
                InlineKeyboardButton(
                    f"🔓 إلغاء حظر {name} / Unban",
                    callback_data=f"admin_unban_{u['user_id']}",
                )
            ])
        else:
            buttons.append([
                InlineKeyboardButton(
                    f"🚫 حظر {name} / Ban",
                    callback_data=f"admin_ban_{u['user_id']}",
                )
            ])

    # أزرار التنقل بين الصفحات
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ السابق / Prev", callback_data=f"admin_users_{page - 1}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("➡️ التالي / Next", callback_data=f"admin_users_{page + 1}")
        )
    if nav_buttons:
        buttons.append(nav_buttons)

    # صف الصفحة الحالية والرجوع
    buttons.append([
        InlineKeyboardButton(
            f"📄 {page + 1}/{total_pages}", callback_data="admin_noop"
        ),
        InlineKeyboardButton("🔙 رجوع / Back", callback_data="admin_panel"),
    ])

    text = "\n".join(lines)
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )


@admin_required
async def ban_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """حظر مستخدم"""
    query = update.callback_query
    await query.answer("🚫 تم الحظر / Banned")

    target_id = int(query.data.split("_")[-1])
    await ban_user(target_id)

    # إعادة تحميل نفس الصفحة
    # نستخرج الصفحة الحالية من السياق (أو نرجع لصفحة 0)
    await query.edit_message_text(
        f"🚫 تم حظر المستخدم / User {target_id} banned\n\n"
        "اضغط للرجوع لقائمة المستخدمين",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 المستخدمين / Users", callback_data="admin_users_0")],
            [InlineKeyboardButton("🔙 رجوع / Back", callback_data="admin_panel")],
        ]),
        parse_mode="HTML",
    )


@admin_required
async def unban_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إلغاء حظر مستخدم"""
    query = update.callback_query
    await query.answer("🔓 تم إلغاء الحظر / Unbanned")

    target_id = int(query.data.split("_")[-1])
    await unban_user(target_id)

    await query.edit_message_text(
        f"🔓 تم إلغاء حظر المستخدم / User {target_id} unbanned\n\n"
        "اضغط للرجوع لقائمة المستخدمين",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("👥 المستخدمين / Users", callback_data="admin_users_0")],
            [InlineKeyboardButton("🔙 رجوع / Back", callback_data="admin_panel")],
        ]),
        parse_mode="HTML",
    )


# ──────────────── كولباك فاضي (للأزرار اللي مش بتعمل حاجة) ────────────────

async def noop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """كولباك فاضي – مبيعملش حاجة (زي رقم الصفحة)"""
    await update.callback_query.answer()


# ──────────────── إلغاء المحادثة ────────────────

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """إلغاء أي ConversationHandler نشط"""
    await update.message.reply_text("❌ تم الإلغاء / Cancelled")
    return ConversationHandler.END


# ════════════════════════════════════════════════════════════════
#  تسجيل كل هاندلرز الأدمن
# ════════════════════════════════════════════════════════════════

def register_admin_handlers(app) -> None:
    """تسجيل كل هاندلرز الأدمن في الأبليكيشن"""

    # أمر /admin
    app.add_handler(CommandHandler("admin", admin_command))

    # كولباك القائمة الرئيسية للأدمن
    app.add_handler(CallbackQueryHandler(admin_menu_callback, pattern=r"^admin_panel$"))

    # الإحصائيات
    app.add_handler(CallbackQueryHandler(admin_stats, pattern=r"^admin_stats$"))

    # المدفوعات المعلقة
    app.add_handler(CallbackQueryHandler(pending_payments, pattern=r"^admin_pending$"))

    # تأكيد دفعة
    app.add_handler(CallbackQueryHandler(confirm_payment, pattern=r"^admin_confirm_\d+$"))

    # رفض دفعة (ConversationHandler لاستلام السبب)
    reject_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(reject_payment_start, pattern=r"^admin_reject_\d+$"),
        ],
        states={
            REJECT_REASON: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, reject_payment_reason),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_message=False,
    )
    app.add_handler(reject_conv)

    # إضافة برنامج (ConversationHandler)
    add_prog_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_program_start, pattern=r"^admin_add_prog$"),
        ],
        states={
            ADD_PROG_NAME_EN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_prog_name_en),
            ],
            ADD_PROG_NAME_AR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_prog_name_ar),
            ],
            ADD_PROG_DESC_EN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_prog_desc_en),
            ],
            ADD_PROG_DESC_AR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_prog_desc_ar),
            ],
            ADD_PROG_CATEGORY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_prog_category),
            ],
            ADD_PROG_VERSION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_prog_version),
            ],
            ADD_PROG_CONFIRM: [
                CallbackQueryHandler(add_prog_confirm, pattern=r"^admin_prog_(save|cancel)$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_message=False,
    )
    app.add_handler(add_prog_conv)

    # إضافة ملف (ConversationHandler)
    add_file_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(add_file_start, pattern=r"^admin_add_file$"),
        ],
        states={
            ADD_FILE_SELECT_PROG: [
                CallbackQueryHandler(
                    add_file_select_prog,
                    pattern=r"^admin_file(for_\d+|_cancel)$",
                ),
            ],
            ADD_FILE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_file_name),
            ],
            ADD_FILE_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_file_url),
            ],
            ADD_FILE_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_file_password),
            ],
            ADD_FILE_VERSION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_file_version),
            ],
            ADD_FILE_SIZE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_file_size),
            ],
            ADD_FILE_CONFIRM: [
                CallbackQueryHandler(add_file_confirm, pattern=r"^admin_file_(save|cancel)$"),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_message=False,
    )
    app.add_handler(add_file_conv)

    # تحديث باسوورد (ConversationHandler)
    upd_pass_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(update_password_start, pattern=r"^admin_upd_pass$"),
        ],
        states={
            UPD_PASS_SELECT_PROG: [
                CallbackQueryHandler(
                    upd_pass_select_prog,
                    pattern=r"^admin_updp_(\d+|cancel)$",
                ),
            ],
            UPD_PASS_SELECT_FILE: [
                CallbackQueryHandler(
                    upd_pass_select_file,
                    pattern=r"^admin_updpf_(\d+|cancel2)$",
                ),
            ],
            UPD_PASS_ENTER: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, upd_pass_enter),
            ],
            UPD_PASS_CONFIRM: [
                CallbackQueryHandler(
                    upd_pass_confirm,
                    pattern=r"^admin_updp_(confirm|cancel3)$",
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_message=False,
    )
    app.add_handler(upd_pass_conv)

    # إذاعة (ConversationHandler)
    broadcast_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(broadcast_start, pattern=r"^admin_broadcast$"),
        ],
        states={
            BROADCAST_MSG: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, broadcast_message),
            ],
            BROADCAST_CONFIRM: [
                CallbackQueryHandler(
                    broadcast_confirm,
                    pattern=r"^admin_bc_(send|cancel)$",
                ),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)],
        per_message=False,
    )
    app.add_handler(broadcast_conv)

    # قائمة المستخدمين
    app.add_handler(CallbackQueryHandler(user_list, pattern=r"^admin_users_\d+$"))

    # حظر/إلغاء حظر
    app.add_handler(CallbackQueryHandler(ban_user_handler, pattern=r"^admin_ban_\d+$"))
    app.add_handler(CallbackQueryHandler(unban_user_handler, pattern=r"^admin_unban_\d+$"))

    # كولباك فاضي
    app.add_handler(CallbackQueryHandler(noop_callback, pattern=r"^admin_noop$"))
