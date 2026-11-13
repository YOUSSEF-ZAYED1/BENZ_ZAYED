# utils/helpers.py
# أدوات ووظائف مساعدة للبوت

import random
import string
from datetime import datetime
from typing import Optional, Union

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from config import ADMIN_IDS
from utils.texts import get_text


def is_admin(user_id: int) -> bool:
    """بيتحقق لو المستخدم أدمن"""
    return user_id in ADMIN_IDS


def build_main_menu_keyboard(lang: str = "ar") -> InlineKeyboardMarkup:
    """بيبني كيبورد القائمة الرئيسية حسب اللغة"""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(get_text("btn_programs", lang), callback_data="prog_menu"),
        ],
        [
            InlineKeyboardButton(get_text("btn_my_subscription", lang), callback_data="sub_my"),
            InlineKeyboardButton(get_text("btn_subscribe", lang), callback_data="sub_menu"),
        ],
        [
            InlineKeyboardButton(get_text("btn_help", lang), callback_data="menu_help"),
            InlineKeyboardButton(get_text("btn_about", lang), callback_data="menu_about"),
        ],
        [
            InlineKeyboardButton(get_text("btn_language", lang), callback_data="menu_lang"),
        ],
    ])


def format_date(dt: Optional[Union[datetime, str]], lang: str = "ar") -> str:
    """بيفورمات التاريخ سواء كان datetime أو نص ISO"""
    if not dt:
        return "—"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt[:16]
    if lang == "ar":
        return dt.strftime("%Y/%m/%d %H:%M")
    return dt.strftime("%d/%m/%Y %H:%M")


def is_subscription_active(end_date: str) -> bool:
    """بيتشيك لو الاشتراك لسه شغال ومنتهيش"""
    try:
        end_dt = datetime.fromisoformat(end_date)
        return datetime.now() < end_dt
    except (ValueError, TypeError):
        return False


def generate_password(length: int = 12) -> str:
    """بيولّد باسورد عشوائي من حروف وأرقام"""
    characters = string.ascii_letters + string.digits
    return "".join(random.choice(characters) for _ in range(length))


def format_file_size(size_str: Optional[str]) -> str:
    """بيفورمات حجم الملف بشكل مقروء"""
    if not size_str:
        return "N/A"
    return size_str
