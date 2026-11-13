# database.py
# موديول قاعدة البيانات - كل العمليات على SQLite

import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from config import DATABASE_PATH, SUBSCRIPTION_PLANS, PAYMENT_METHODS

logger = logging.getLogger(__name__)


def _get_connection() -> sqlite3.Connection:
    """بيرجع كونكشن لقاعدة البيانات مع تفعيل المفاتيح الأجنبية"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _execute(
    query: str,
    params: Tuple = (),
    fetch_one: bool = False,
    fetch_all: bool = False,
) -> Any:
    """دالة مساعدة لتنفيذ استعلامات SQLite بشكل آمن"""
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = _get_connection()
        cursor = conn.execute(query, params)
        if fetch_one:
            row = cursor.fetchone()
            return dict(row) if row else None
        if fetch_all:
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        conn.commit()
        return cursor.lastrowid
    except sqlite3.Error as e:
        logger.error("Database error: %s | Query: %s", e, query)
        if conn:
            conn.rollback()
        return None
    finally:
        if conn:
            conn.close()


# ═══════════════════════════════════════════════
#  تهيئة قاعدة البيانات والبرامج الافتراضية
# ═══════════════════════════════════════════════

def init_db() -> None:
    """بينشئ الجداول ويضيف برامج مرسيدس الأساسية لو قاعدة البيانات فاضية"""
    conn: Optional[sqlite3.Connection] = None
    try:
        conn = _get_connection()
        cursor = conn.cursor()

        # جدول المستخدمين (المفتاح الرئيسي هو user_id بتاع تليجرام)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id    INTEGER PRIMARY KEY,
                username   TEXT,
                first_name TEXT,
                last_name  TEXT,
                lang       TEXT    DEFAULT 'ar',
                joined_at  TEXT    DEFAULT (datetime('now')),
                is_banned  INTEGER DEFAULT 0
            )
        """)

        # جدول البرامج
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS programs (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                name_en        TEXT    NOT NULL,
                name_ar        TEXT    NOT NULL,
                description_en TEXT,
                description_ar TEXT,
                category       TEXT,
                version        TEXT,
                is_active      INTEGER DEFAULT 1,
                created_at     TEXT    DEFAULT (datetime('now'))
            )
        """)

        # جدول الملفات (كل نسخة ليها رابط وباسوورد خاص)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS files (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                program_id   INTEGER NOT NULL,
                file_name    TEXT    NOT NULL,
                download_url TEXT    NOT NULL,
                password     TEXT,
                version      TEXT,
                size_info    TEXT,
                is_active    INTEGER DEFAULT 1,
                created_at   TEXT    DEFAULT (datetime('now')),
                updated_at   TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (program_id) REFERENCES programs(id) ON DELETE CASCADE
            )
        """)

        # جدول الاشتراكات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subscriptions (
                id             INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id        INTEGER NOT NULL,
                plan_type      TEXT    NOT NULL,
                start_date     TEXT    NOT NULL,
                end_date       TEXT    NOT NULL,
                is_active      INTEGER DEFAULT 1,
                payment_method TEXT,
                payment_ref    TEXT,
                created_at     TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """)

        # جدول المدفوعات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id           INTEGER NOT NULL,
                subscription_id   INTEGER,
                plan_id           INTEGER NOT NULL,
                plan_type         TEXT    NOT NULL,
                amount            REAL    DEFAULT 0,
                currency          TEXT    DEFAULT 'USD',
                payment_method_id INTEGER,
                payment_method    TEXT,
                payment_ref       TEXT,
                status            TEXT    DEFAULT 'pending',
                proof_file_id     TEXT,
                admin_note        TEXT,
                created_at        TEXT    DEFAULT (datetime('now')),
                confirmed_at      TEXT,
                confirmed_by      INTEGER,
                FOREIGN KEY (user_id)         REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (subscription_id) REFERENCES subscriptions(id) ON DELETE SET NULL
            )
        """)

        # جدول سجل التحميلات
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS download_logs (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL,
                file_id       INTEGER NOT NULL,
                downloaded_at TEXT    DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                FOREIGN KEY (file_id) REFERENCES files(id) ON DELETE CASCADE
            )
        """)

        # إضافة برامج مرسيدس الأساسية لو الجدول فاضي لأول مرة
        count_row = cursor.execute("SELECT COUNT(*) as cnt FROM programs").fetchone()
        if count_row and count_row["cnt"] == 0:
            starter_programs = [
                (
                    "Xentry Diagnosis (XDOS / PassThru)",
                    "Xentry Diagnosis (تشخيص مرسيدس)",
                    "Official Mercedes-Benz diagnostic software for all models.",
                    "برنامج التشخيص الرسمي لسيارات مرسيدس بنز بجميع الموديلات.",
                    "Diagnostic",
                    "2025/2026",
                ),
                (
                    "DTS Monaco",
                    "DTS Monaco (برمجة وتكويد)",
                    "Advanced engineering & SCN/variant coding tool for Mercedes ECUs.",
                    "أداة البرمجة والتكويد المتقدمة لوحدات التحكم (ECU) لمرسيدس.",
                    "Coding & Engineering",
                    "9.02 / 8.16",
                ),
                (
                    "Vediamo",
                    "Vediamo (هندسة وبرمجة)",
                    "Engineering software for direct ECU flashing and coding.",
                    "برنامج الهندسة والبرمجة المباشرة لوحدات مرسيدس.",
                    "Coding & Engineering",
                    "05.01.01",
                ),
                (
                    "EPC / WIS / ASRA",
                    "EPC / WIS (كتالوج قطع الغيار والصيانة)",
                    "Electronic Parts Catalog & Workshop Information System.",
                    "كتالوج قطع الغيار الإلكتروني ودليل الصيانة والرسومات الهندسية.",
                    "Parts & Manuals",
                    "Latest",
                ),
            ]
            cursor.executemany(
                """
                INSERT INTO programs
                    (name_en, name_ar, description_en, description_ar, category, version)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                starter_programs,
            )

        conn.commit()
        logger.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logger.error("Failed to initialize database: %s", e)
        raise
    finally:
        if conn:
            conn.close()


# ═══════════════════════════════════════════════
#  عمليات المستخدمين (Users)
# ═══════════════════════════════════════════════

async def get_user(user_id: int) -> Optional[Dict[str, Any]]:
    """بيجيب بيانات مستخدم بأيدي التليجرام"""
    return _execute(
        "SELECT * FROM users WHERE user_id = ?",
        (user_id,),
        fetch_one=True,
    )


async def create_user(
    user_id: int,
    username: Optional[str] = None,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    lang: str = "ar",
) -> Optional[int]:
    """بيسجل مستخدم جديد أو يتجاهل لو مسجل قبل كده"""
    return _execute(
        """
        INSERT OR IGNORE INTO users (user_id, username, first_name, last_name, lang)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, username, first_name, last_name, lang),
    )


async def update_user_language(user_id: int, lang: str) -> Optional[int]:
    """بيغيّر لغة المستخدم"""
    return _execute(
        "UPDATE users SET lang = ? WHERE user_id = ?",
        (lang, user_id),
    )


async def ban_user(user_id: int) -> Optional[int]:
    """بيحظر مستخدم"""
    return _execute(
        "UPDATE users SET is_banned = 1 WHERE user_id = ?",
        (user_id,),
    )


async def unban_user(user_id: int) -> Optional[int]:
    """بيرفع الحظر عن مستخدم"""
    return _execute(
        "UPDATE users SET is_banned = 0 WHERE user_id = ?",
        (user_id,),
    )


async def get_all_users() -> List[Dict[str, Any]]:
    """بيرجع كل المستخدمين"""
    result = _execute("SELECT * FROM users ORDER BY joined_at DESC", fetch_all=True)
    return result if result else []


async def get_users_paginated(page: int = 0, per_page: int = 10) -> Dict[str, Any]:
    """بيرجع صفحة من المستخدمين مع العدد الكلي"""
    offset = max(0, page) * per_page
    total_row = _execute("SELECT COUNT(*) as cnt FROM users", fetch_one=True)
    total = total_row["cnt"] if total_row else 0
    users = _execute(
        "SELECT * FROM users ORDER BY joined_at DESC LIMIT ? OFFSET ?",
        (per_page, offset),
        fetch_all=True,
    )
    return {"users": users or [], "total": total}


# ═══════════════════════════════════════════════
#  عمليات البرامج والملفات (Programs & Files)
# ═══════════════════════════════════════════════

async def get_active_programs() -> List[Dict[str, Any]]:
    """بيرجع كل البرامج الفعّالة"""
    result = _execute(
        "SELECT * FROM programs WHERE is_active = 1 ORDER BY id ASC",
        fetch_all=True,
    )
    return result if result else []


async def get_program_by_id(program_id: int) -> Optional[Dict[str, Any]]:
    """بيجيب برنامج بالأيدي"""
    return _execute(
        "SELECT * FROM programs WHERE id = ?",
        (program_id,),
        fetch_one=True,
    )


async def create_program(
    name_en: str,
    name_ar: str,
    description_en: str = "",
    description_ar: str = "",
    category: str = "",
    version: str = "1.0",
) -> Optional[int]:
    """بيضيف برنامج جديد"""
    return _execute(
        """
        INSERT INTO programs (name_en, name_ar, description_en, description_ar, category, version)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (name_en, name_ar, description_en, description_ar, category, version),
    )


async def get_program_files(program_id: int) -> List[Dict[str, Any]]:
    """بيرجع ملفات برنامج معين"""
    result = _execute(
        "SELECT * FROM files WHERE program_id = ? AND is_active = 1 ORDER BY id DESC",
        (program_id,),
        fetch_all=True,
    )
    return result if result else []


async def get_file_by_id(file_id: int) -> Optional[Dict[str, Any]]:
    """بيجيب بيانات ملف بالأيدي"""
    return _execute(
        "SELECT * FROM files WHERE id = ?",
        (file_id,),
        fetch_one=True,
    )


async def create_file_record(
    program_id: int,
    file_name: str,
    download_url: str,
    password: Optional[str] = None,
    version: str = "1.0",
    size_info: Optional[str] = None,
) -> Optional[int]:
    """بيضيف ملف جديد لبرنامج"""
    return _execute(
        """
        INSERT INTO files (program_id, file_name, download_url, password, version, size_info)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (program_id, file_name, download_url, password, version, size_info),
    )


async def update_file_password(file_id: int, password: str) -> Optional[int]:
    """بيحدّث باسوورد نسخة/ملف"""
    return _execute(
        "UPDATE files SET password = ?, updated_at = datetime('now') WHERE id = ?",
        (password, file_id),
    )


# ═══════════════════════════════════════════════
#  خطط الاشتراك وطرق الدفع
# ═══════════════════════════════════════════════

async def get_subscription_plans() -> List[Dict[str, Any]]:
    """بيرجع خطط الاشتراك من الإعدادات"""
    return SUBSCRIPTION_PLANS


async def get_payment_methods() -> List[Dict[str, Any]]:
    """بيرجع طرق الدفع المتاحة من الإعدادات"""
    return PAYMENT_METHODS


# ═══════════════════════════════════════════════
#  المدفوعات والاشتراكات
# ═══════════════════════════════════════════════

async def create_payment_record(
    user_id: int,
    plan_id: int,
    payment_method_id: int,
    proof_file_id: Optional[str] = None,
    status: str = "pending",
    payment_ref: Optional[str] = None,
) -> Optional[int]:
    """بيسجل طلب دفع جديد"""
    plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == plan_id), None)
    method = next((m for m in PAYMENT_METHODS if m["id"] == payment_method_id), None)

    plan_type = plan["type"] if plan else "monthly"
    amount = plan["price"] if plan else 0.0
    currency = plan["currency"] if plan else "USD"
    method_key = method["key"] if method else str(payment_method_id)

    return _execute(
        """
        INSERT INTO payments
            (user_id, plan_id, plan_type, amount, currency,
             payment_method_id, payment_method, payment_ref, status, proof_file_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            plan_id,
            plan_type,
            amount,
            currency,
            payment_method_id,
            method_key,
            payment_ref,
            status,
            proof_file_id,
        ),
    )


async def get_pending_payments() -> List[Dict[str, Any]]:
    """بيرجع كل المدفوعات المعلقة"""
    result = _execute(
        "SELECT * FROM payments WHERE status = 'pending' ORDER BY created_at ASC",
        fetch_all=True,
    )
    return result if result else []


async def get_payment_by_id(payment_id: int) -> Optional[Dict[str, Any]]:
    """بيجيب دفعة بالأيدي"""
    return _execute(
        "SELECT * FROM payments WHERE id = ?",
        (payment_id,),
        fetch_one=True,
    )


async def confirm_payment_record(
    payment_id: int,
    admin_id: Optional[int] = None,
) -> Optional[Dict[str, Any]]:
    """بيأكد الدفعة وبيفعل الاشتراك للمستخدم وبيرجع بيانات الاشتراك"""
    payment = await get_payment_by_id(payment_id)
    if not payment:
        return None

    plan = next((p for p in SUBSCRIPTION_PLANS if p["id"] == payment["plan_id"]), None)
    duration_days = plan["duration_days"] if plan else 30

    # لو المستخدم عنده اشتراك فعّال حالياً نمددله من تاريخ الانتهاء
    existing_sub = await get_active_subscription(payment["user_id"])
    now = datetime.now()
    if existing_sub:
        try:
            base_date = max(now, datetime.fromisoformat(existing_sub["end_date"]))
        except ValueError:
            base_date = now
    else:
        base_date = now

    start_date = now.isoformat()
    end_date = (base_date + timedelta(days=duration_days)).isoformat()

    sub_id = _execute(
        """
        INSERT INTO subscriptions (user_id, plan_type, start_date, end_date, payment_method, payment_ref)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            payment["user_id"],
            payment["plan_type"],
            start_date,
            end_date,
            payment.get("payment_method"),
            payment.get("payment_ref"),
        ),
    )

    _execute(
        """
        UPDATE payments
        SET status = 'confirmed', confirmed_at = ?, confirmed_by = ?, subscription_id = ?
        WHERE id = ?
        """,
        (now.isoformat(), admin_id, sub_id, payment_id),
    )

    return _execute("SELECT * FROM subscriptions WHERE id = ?", (sub_id,), fetch_one=True)


async def reject_payment_record(
    payment_id: int,
    reason: str = "",
    admin_id: Optional[int] = None,
) -> Optional[int]:
    """بيرفض الدفعة مع حفظ سبب الرفض"""
    return _execute(
        """
        UPDATE payments
        SET status = 'rejected', admin_note = ?, confirmed_by = ?
        WHERE id = ?
        """,
        (reason, admin_id, payment_id),
    )


async def get_active_subscription(user_id: int) -> Optional[Dict[str, Any]]:
    """بيجيب الاشتراك الفعّال للمستخدم"""
    sub = _execute(
        """
        SELECT * FROM subscriptions
        WHERE user_id = ? AND is_active = 1
        ORDER BY end_date DESC LIMIT 1
        """,
        (user_id,),
        fetch_one=True,
    )
    if not sub:
        return None
    try:
        if datetime.fromisoformat(sub["end_date"]) > datetime.now():
            return sub
    except ValueError:
        pass
    return None


# ═══════════════════════════════════════════════
#  سجل التحميلات والإحصائيات
# ═══════════════════════════════════════════════

async def log_download(user_id: int, file_id: int) -> Optional[int]:
    """بيسجل عملية تحميل ملف"""
    return _execute(
        "INSERT INTO download_logs (user_id, file_id) VALUES (?, ?)",
        (user_id, file_id),
    )


async def get_stats() -> Dict[str, Any]:
    """بيرجع إحصائيات البوت للوحة الأدمن"""
    total_users = _execute("SELECT COUNT(*) as cnt FROM users", fetch_one=True)
    active_subs = _execute(
        "SELECT COUNT(*) as cnt FROM subscriptions WHERE is_active = 1 AND end_date > ?",
        (datetime.now().isoformat(),),
        fetch_one=True,
    )
    pending_pay = _execute(
        "SELECT COUNT(*) as cnt FROM payments WHERE status = 'pending'",
        fetch_one=True,
    )
    total_dl = _execute("SELECT COUNT(*) as cnt FROM download_logs", fetch_one=True)
    revenue = _execute(
        "SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = 'confirmed'",
        fetch_one=True,
    )
    return {
        "total_users": total_users["cnt"] if total_users else 0,
        "active_subscriptions": active_subs["cnt"] if active_subs else 0,
        "pending_payments": pending_pay["cnt"] if pending_pay else 0,
        "total_downloads": total_dl["cnt"] if total_dl else 0,
        "total_revenue": revenue["total"] if revenue else 0.0,
    }
