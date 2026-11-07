"""
database.py — нормалізована схема БД та всі функції роботи з даними.

Схема:
  users    — облікові записи (викладачі та студенти)
  groups   — навчальні групи
  subjects — предмети
  students — студенти (пов'язані з групою)
  grades   — оцінки (студент × предмет × дата)
"""
import os
import hashlib
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime

from config import LOCAL_DB, REMOTE_DB

os.makedirs("data", exist_ok=True)
local_engine = create_engine(LOCAL_DB)

# ── Ініціалізація схеми ────────────────────────────────────────────────────────
_SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role          TEXT NOT NULL CHECK(role IN ('teacher','student')),
    full_name     TEXT NOT NULL,
    created_at    TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS groups (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS subjects (
    id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL
);

CREATE TABLE IF NOT EXISTS students (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name  TEXT NOT NULL,
    group_id   INTEGER NOT NULL REFERENCES groups(id),
    user_id    INTEGER REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS grades (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  INTEGER NOT NULL REFERENCES students(id),
    subject_id  INTEGER NOT NULL REFERENCES subjects(id),
    grade       REAL    NOT NULL,
    upload_date TEXT    NOT NULL,
    synced      INTEGER DEFAULT 0
);
"""

with local_engine.connect() as conn:
    for stmt in _SCHEMA.strip().split(";"):
        stmt = stmt.strip()
        if stmt:
            conn.execute(text(stmt))
    conn.commit()

# ── Seed: адмін за замовчуванням ──────────────────────────────────────────────
def _hash(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()

with local_engine.connect() as conn:
    exists = conn.execute(text("SELECT 1 FROM users WHERE username='admin'")).fetchone()
    if not exists:
        conn.execute(text(
            "INSERT INTO users (username, password_hash, role, full_name) VALUES "
            "('admin', :h, 'teacher', 'Адміністратор')"
        ), {"h": _hash("admin2026")})
        conn.commit()

# ── Авторизація ───────────────────────────────────────────────────────────────
def authenticate(username: str, password: str) -> dict | None:
    """Повертає словник з даними користувача або None якщо невірні дані."""
    row = None
    with local_engine.connect() as conn:
        row = conn.execute(text(
            "SELECT id, username, role, full_name FROM users "
            "WHERE username=:u AND password_hash=:p"
        ), {"u": username.strip(), "p": _hash(password)}).fetchone()
    if row:
        return {"id": row[0], "username": row[1], "role": row[2], "full_name": row[3]}
    return None


def register_user(username: str, password: str, role: str, full_name: str) -> tuple[bool, str]:
    """Реєструє нового користувача. Повертає (успіх, повідомлення)."""
    try:
        with local_engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO users (username, password_hash, role, full_name) VALUES "
                "(:u, :p, :r, :n)"
            ), {"u": username.strip(), "p": _hash(password), "r": role, "n": full_name.strip()})
            conn.commit()
        return True, f"Користувача «{username}» створено"
    except Exception as e:
        return False, f"Помилка: {e}"


def list_users() -> pd.DataFrame:
    return pd.read_sql(
        "SELECT id, username, role, full_name, created_at FROM users ORDER BY id",
        local_engine
    )


def delete_user(user_id: int) -> None:
    with local_engine.connect() as conn:
        conn.execute(text("DELETE FROM users WHERE id=:id AND username!='admin'"), {"id": user_id})
        conn.commit()

# ── Допоміжні: отримати або створити запис ─────────────────────────────────────
def _get_or_create(conn, table: str, col: str, val: str) -> int:
    row = conn.execute(text(f"SELECT id FROM {table} WHERE {col}=:v"), {"v": val}).fetchone()
    if row:
        return row[0]
    result = conn.execute(text(f"INSERT INTO {table} ({col}) VALUES (:v)"), {"v": val})
    conn.commit()
    return result.lastrowid


def _get_or_create_student(conn, full_name: str, group_id: int) -> int:
    row = conn.execute(text(
        "SELECT id FROM students WHERE full_name=:n AND group_id=:g"
    ), {"n": full_name, "g": group_id}).fetchone()
    if row:
        return row[0]
    result = conn.execute(text(
        "INSERT INTO students (full_name, group_id) VALUES (:n, :g)"
    ), {"n": full_name, "g": group_id})
    conn.commit()
    return result.lastrowid

# ── Збереження та читання оцінок ──────────────────────────────────────────────
def save_grades(df: pd.DataFrame, upload_date: str | None = None) -> int:
    """
    Зберігає датафрейм з колонками (group_name, student_name, topic, grade)
    у нормалізовані таблиці. Повертає кількість збережених рядків.
    upload_date — рядок дати у форматі YYYY-MM-DD, або None (тоді береться поточний час).
    """
    upload_date = upload_date or datetime.now().isoformat()
    count = 0
    with local_engine.connect() as conn:
        for _, row in df.iterrows():
            group_id   = _get_or_create(conn, "groups",   "name", row["group_name"])
            subject_id = _get_or_create(conn, "subjects", "name", row["topic"])
            student_id = _get_or_create_student(conn, row["student_name"], group_id)
            conn.execute(text(
                "INSERT INTO grades (student_id, subject_id, grade, upload_date, synced) "
                "VALUES (:st, :su, :g, :d, 0)"
            ), {"st": student_id, "su": subject_id, "g": float(row["grade"]), "d": upload_date})
            count += 1
        conn.commit()
    return count


def load_grades() -> pd.DataFrame:
    """Повертає денормалізований датафрейм для аналітики."""
    sql = """
        SELECT
            gr.name       AS group_name,
            st.full_name  AS student_name,
            su.name       AS topic,
            g.grade,
            g.upload_date,
            g.synced,
            g.id          AS grade_id
        FROM grades g
        JOIN students st ON g.student_id = st.id
        JOIN groups   gr ON st.group_id  = gr.id
        JOIN subjects su ON g.subject_id = su.id
        ORDER BY g.upload_date DESC
    """
    try:
        df = pd.read_sql(sql, local_engine)
        if not df.empty:
            df["upload_date"] = pd.to_datetime(df["upload_date"])
        return df
    except Exception:
        return pd.DataFrame()


def clear_grades() -> None:
    with local_engine.connect() as conn:
        conn.execute(text("DELETE FROM grades"))
        conn.commit()


def count_unsynced() -> int:
    try:
        r = pd.read_sql("SELECT COUNT(*) as n FROM grades WHERE synced=0", local_engine)
        return int(r["n"].iloc[0])
    except Exception:
        return 0

# ── Синхронізація з PostgreSQL ────────────────────────────────────────────────
def is_remote_available() -> bool:
    try:
        from sqlalchemy import create_engine as ce
        eng = ce(REMOTE_DB, connect_args={"connect_timeout": 3})
        with eng.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


def sync_to_remote() -> tuple[bool, str]:
    try:
        df = load_grades()
        unsynced = df[df["synced"] == 0]
        if unsynced.empty:
            return False, "Немає нових даних для синхронізації"
        from sqlalchemy import create_engine as ce
        remote = ce(REMOTE_DB)
        send = unsynced[["group_name", "student_name", "topic", "grade", "upload_date"]].copy()
        send.to_sql("grades_flat", remote, if_exists="append", index=False)
        with local_engine.connect() as conn:
            conn.execute(text("UPDATE grades SET synced=1 WHERE synced=0"))
            conn.commit()
        return True, f"Відправлено {len(unsynced)} записів"
    except Exception as e:
        return False, f"Помилка: {e}"


# ── Прив'язка студента-користувача ────────────────────────────────────────────
def link_student_user(student_full_name: str, user_id: int) -> bool:
    """Прив'язує обліковий запис до запису студента за повним іменем."""
    try:
        with local_engine.connect() as conn:
            conn.execute(text(
                "UPDATE students SET user_id=:uid WHERE full_name=:name"
            ), {"uid": user_id, "name": student_full_name})
            conn.commit()
        return True
    except Exception:
        return False


def get_student_by_user_id(user_id: int) -> str | None:
    """Повертає full_name студента за user_id."""
    with local_engine.connect() as conn:
        row = conn.execute(text(
            "SELECT full_name FROM students WHERE user_id=:uid"
        ), {"uid": user_id}).fetchone()
    return row[0] if row else None