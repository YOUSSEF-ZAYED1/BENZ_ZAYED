"""
handlers/subscription.py
هاندلرز الاشتراك والدفع (يدوي + أوتوماتيك) وإرسال إثبات الدفع
"""

import html
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.ext import (
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    PreCheckoutQueryHandler,
    filters,
)

from database import (
    get_user,
    get_subscription_plans,
    get_payment_methods,
    create_payment_record,
    confirm_payment_record,
    get_active_subscription,
)
from config import ADMIN_IDS, PAYMENT_PROVIDER_TOKEN, SUPPORT_USERNAME
from utils.texts import get_text
from utils.helpers import format_date


# ──────────────────────────── قائمة الاشتراك ────────────────────────────

async def subscribe_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض خطط الاشتراك المتاحة (شهري / سنوي)"""
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

    plans = await get_subscription_plans()

    if not plans:
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(
                get_text("btn_back_menu", lang),
                callback_data="back_menu",
            )]
        ])
        await query.edit_message_text(
            get_text("no_plans", lang),
            reply_markup=keyboard,
            parse_mode="HTML",
        )
        return

    buttons = []
    for plan in plans:
        name = plan.get(f"name_{lang}") or get_text(f"plan_{plan['type']}", lang)
        price = plan.get("price", 0)
        currency = plan.get("currency", "USD")
        label = f"{name} — {price:g} {currency}"
        buttons.append([
            InlineKeyboardButton(label, callback_data=f"sub_plan_{plan['id']}")
        ])

    buttons.append([
        InlineKeyboardButton(
            get_text("btn_back_menu", lang),
            callback_data="back_menu",
        )
    ])

    await query.edit_message_text(
        get_text("choose_plan", lang),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )


# ──────────────────────────── اختيار خطة ────────────────────────────

async def choose_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بعد اختيار الخطة → عرض طرق الدفع (يدوي + أونلاين)"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    plan_id = int(query.data.split("_")[-1])
    context.user_data["selected_plan_id"] = plan_id

    methods = await get_payment_methods()

    buttons = []
    # لو توكن بوابة الدفع بتاع تليجرام متضاف نعرض الدفع الفوري بالكارت
    if PAYMENT_PROVIDER_TOKEN:
        buttons.append([
            InlineKeyboardButton(
                get_text("btn_pay_online_card", lang),
                callback_data=f"pay_tg_{plan_id}",
            )
        ])

    for method in methods:
        label = method.get(f"name_{lang}", method.get("name_en", "—"))
        buttons.append([
            InlineKeyboardButton(label, callback_data=f"pay_method_{method['id']}")
        ])

    buttons.append([
        InlineKeyboardButton(
            get_text("btn_back_menu", lang),
            callback_data="sub_menu",
        )
    ])

    await query.edit_message_text(
        get_text("choose_payment", lang),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )


# ──────────────────────────── الدفع الفوري عبر تليجرام (اختياري) ────────────────────────────

async def send_telegram_invoice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """إرسال فاتورة دفع أوتوماتيك عبر Telegram Payments لو التوكن متفعل"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    plan_id = int(query.data.split("_")[-1])
    plans = await get_subscription_plans()
    plan = next((p for p in plans if p["id"] == plan_id), None)
    if not plan or not PAYMENT_PROVIDER_TOKEN:
        return

    title = plan.get(f"name_{lang}") or get_text(f"plan_{plan['type']}", lang)
    price_cents = int(round(float(plan["price"]) * 100))

    await context.bot.send_invoice(
        chat_id=user_id,
        title=title,
        description="Mercedes Software Subscription",
        payload=f"sub_plan_{plan_id}",
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency=plan.get("currency", "USD"),
        prices=[LabeledPrice(label=title, amount=price_cents)],
    )


async def precheckout_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تأكيد جاهزية الفاتورة قبل الخصم"""
    query = update.pre_checkout_query
    await query.answer(ok=True)


async def successful_payment_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """تفعيل الاشتراك أوتوماتيكياً فور نجاح الدفع بالكارت"""
    user_id = update.effective_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    sp = update.message.successful_payment
    plan_id = int(sp.invoice_payload.split("_")[-1])

    payment_id = await create_payment_record(
        user_id=user_id,
        plan_id=plan_id,
        payment_method_id=0,
        status="pending",
        payment_ref=sp.telegram_payment_charge_id,
    )
    subscription = await confirm_payment_record(payment_id)

    if subscription:
        end_date = format_date(subscription.get("end_date"), lang)
        plan_type = get_text(f"plan_{subscription.get('plan_type', 'monthly')}", lang)
        text = get_text("payment_confirmed", lang).format(
            plan_type=plan_type,
            end_date=end_date,
        )
    else:
        text = get_text("payment_confirmed_simple", lang)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(get_text("btn_programs", lang), callback_data="prog_menu")],
        [InlineKeyboardButton(get_text("btn_back_menu", lang), callback_data="back_menu")],
    ])
    await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")


# ──────────────────────────── اختيار طريقة الدفع ────────────────────────────

async def choose_payment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """بعد اختيار طريقة الدفع → عرض تعليمات الدفع وطلب إثبات"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    method_id = int(query.data.split("_")[-1])
    context.user_data["selected_payment_method"] = method_id
    context.user_data["awaiting_proof"] = True

    methods = await get_payment_methods()
    method = next((m for m in methods if m["id"] == method_id), None)

    if not method:
        await query.edit_message_text(get_text("payment_method_not_found", lang))
        return

    plan_id = context.user_data.get("selected_plan_id")
    plans = await get_subscription_plans()
    plan = next((p for p in plans if p["id"] == plan_id), None)
    amount = f"{plan['price']:g}" if plan else "—"
    currency = plan.get("currency", "USD") if plan else "USD"

    method_name = html.escape(method.get(f"name_{lang}", method.get("name_en", "—")))
    account_info = html.escape(method.get("account_info", "—"))
    instructions = html.escape(method.get(f"instructions_{lang}", method.get("instructions_en", "")))

    text = get_text("payment_instructions_template", lang).format(
        method_name=method_name,
        amount=amount,
        currency=currency,
        account_info=account_info,
        instructions=instructions,
    )

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            get_text("btn_cancel", lang),
            callback_data="back_menu",
        )]
    ])

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
        disable_web_page_preview=True,
    )


# ──────────────────────────── استلام إثبات الدفع (صورة أو رقم عملية) ────────────────────────────

async def receive_proof(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """استلام صورة إثبات الدفع أو رقم العملية من المستخدم"""
    if not context.user_data.get("awaiting_proof"):
        return

    user_id = update.effective_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    plan_id = context.user_data.get("selected_plan_id")
    method_id = context.user_data.get("selected_payment_method")

    if not plan_id or not method_id:
        await update.message.reply_text(
            get_text("no_plan_selected", lang),
            parse_mode="HTML",
        )
        return

    file_id = update.message.photo[-1].file_id if update.message.photo else None
    payment_ref = update.message.text.strip() if update.message.text else update.message.caption

    payment_id = await create_payment_record(
        user_id=user_id,
        plan_id=plan_id,
        payment_method_id=method_id,
        proof_file_id=file_id,
        status="pending",
        payment_ref=payment_ref,
    )

    context.user_data["awaiting_proof"] = False
    context.user_data.pop("selected_plan_id", None)
    context.user_data.pop("selected_payment_method", None)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(
            get_text("btn_back_menu", lang),
            callback_data="back_menu",
        )]
    ])

    await update.message.reply_text(
        get_text("proof_received", lang),
        reply_markup=keyboard,
        parse_mode="HTML",
    )

    safe_name = html.escape(update.effective_user.first_name or "—")
    safe_username = html.escape(update.effective_user.username or "—")
    ref_line = f"\n🔖 Ref: <code>{html.escape(payment_ref)}</code>" if payment_ref else ""

    user_info = (
        f"👤 {safe_name} (@{safe_username})\n"
        f"🆔 ID: <code>{user_id}</code>\n"
        f"🧾 Payment #{payment_id}"
        f"{ref_line}"
    )

    admin_keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ تأكيد / Confirm", callback_data=f"admin_confirm_{payment_id}"),
            InlineKeyboardButton("❌ رفض / Reject", callback_data=f"admin_reject_{payment_id}"),
        ]
    ])

    caption = f"💳 <b>دفعة جديدة معلقة / New Pending Payment</b>\n\n{user_info}"

    for admin_id in ADMIN_IDS:
        try:
            if file_id:
                await context.bot.send_photo(
                    chat_id=admin_id,
                    photo=file_id,
                    caption=caption,
                    reply_markup=admin_keyboard,
                    parse_mode="HTML",
                )
            else:
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=caption,
                    reply_markup=admin_keyboard,
                    parse_mode="HTML",
                )
        except Exception:
            pass


# ──────────────────────────── اشتراكي ────────────────────────────

async def my_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """عرض حالة اشتراك المستخدم الحالي"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    db_user = await get_user(user_id)
    lang = db_user.get("lang", "ar") if db_user else "ar"

    subscription = await get_active_subscription(user_id)

    if subscription:
        plan_type = get_text(f"plan_{subscription['plan_type']}", lang)
        start_date = format_date(subscription.get("start_date"), lang)
        end_date = format_date(subscription.get("end_date"), lang)

        text = get_text("subscription_active_template", lang).format(
            status=get_text("status_active", lang),
            plan_type=plan_type,
            start_date=start_date,
            end_date=end_date,
        )
    else:
        text = get_text("no_subscription", lang)

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

    await query.edit_message_text(
        text=text,
        reply_markup=keyboard,
        parse_mode="HTML",
    )


# ──────────────────────────── تسجيل الهاندلرز ────────────────────────────

def register_subscription_handlers(app) -> None:
    """تسجيل كل هاندلرز الاشتراك في الأبليكيشن"""
    app.add_handler(CallbackQueryHandler(subscribe_menu, pattern=r"^sub_menu$"))
    app.add_handler(CallbackQueryHandler(choose_plan, pattern=r"^sub_plan_\d+$"))
    app.add_handler(CallbackQueryHandler(choose_payment, pattern=r"^pay_method_\d+$"))
    app.add_handler(CallbackQueryHandler(send_telegram_invoice, pattern=r"^pay_tg_\d+$"))
    app.add_handler(CallbackQueryHandler(my_subscription, pattern=r"^sub_my$"))
    app.add_handler(PreCheckoutQueryHandler(precheckout_callback))
    app.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, successful_payment_callback))
    # هاندلر استلام إثبات الدفع (صورة أو نص برقم العملية)
    app.add_handler(
        MessageHandler((filters.PHOTO | (filters.TEXT & ~filters.COMMAND)), receive_proof)
    )
