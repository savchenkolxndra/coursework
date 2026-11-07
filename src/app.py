"""
app.py — головний файл застосунку «Аналітика успішності студентів».

Запуск: streamlit run src/app.py
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st

from config import CUSTOM_CSS, DARK_GREEN, MID_GREEN, BG_GREEN, GOLD, GOLD_LIGHT, GOLD_MID
from database import count_unsynced, get_student_by_user_id
from auth import show_login
from pages import analytics, upload, export_page, sync_page, forecasting_page, users_page

# ── Конфігурація ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Аналітика успішності студентів",
    layout="wide",
    page_icon="📊"
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# ── Авторизація ───────────────────────────────────────────────────────────────
if not st.session_state.get("logged_in"):
    show_login()
    st.stop()

role       = st.session_state["role"]
full_name  = st.session_state["full_name"]
user_id    = st.session_state["user_id"]
is_teacher = role == "teacher"

# Для студента визначаємо ім'я в таблиці оцінок
if not is_teacher:
    linked_name = get_student_by_user_id(user_id)
    # Якщо не прив'язаний — шукаємо за full_name
    user_name = linked_name if linked_name else full_name
else:
    user_name = full_name

# ── Сайдбар ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 📊 Аналітика успішності")
    role_label = "Викладач 🎓" if is_teacher else "Студент 👤"
    st.markdown(f"**{role_label}**")
    st.markdown(f"{full_name}")
    st.markdown("---")

    unsynced = count_unsynced()
    sync_lbl = "🔄 Синхронізація" + (f" ({unsynced})" if unsynced else "")

    if is_teacher:
        pages = [
            "🏠 Головна",
            "📤 Завантаження",
            "📈 Аналітика",
            "🔮 Прогнози",
            "📥 Експорт",
            "👥 Користувачі",
            sync_lbl,
        ]
    else:
        pages = ["🏠 Головна", "📈 Аналітика", "🔮 Прогнози"]

    page = st.radio("", pages, label_visibility="collapsed")
    st.markdown("---")

    if st.button("Вийти"):
        for k in ["logged_in", "role", "full_name", "username", "user_id"]:
            st.session_state.pop(k, None)
        st.rerun()

# ── Маршрутизація ─────────────────────────────────────────────────────────────
if "Головна" in page:
    st.title("📊 Аналітика успішності студентів")
    st.markdown(f"Вітаємо, **{full_name}**! Ви увійшли як **{'викладач' if is_teacher else 'студент'}**.")

    cols = st.columns(4)
    cards = [
        (BG_GREEN,    MID_GREEN,  DARK_GREEN, "📤 Завантаження", "CSV та XLSX файли"),
        (GOLD_LIGHT,  GOLD_MID,   GOLD,       "📈 Аналітика",    "8+ типів графіків"),
        (BG_GREEN,    MID_GREEN,  DARK_GREEN, "🔮 Прогнози",     "Лінійна та поліноміальна регресія"),
        (GOLD_LIGHT,  GOLD_MID,   GOLD,       "📥 Експорт",      "PDF, Excel, CSV"),
    ]
    for col, (bg, border, tc, title, sub) in zip(cols, cards):
        col.markdown(f"""
        <div style='background:{bg};border-radius:12px;padding:14px;border:1px solid {border}'>
          <b style='color:{tc}'>{title}</b><br>
          <span style='color:{tc};font-size:12px;opacity:0.85'>{sub}</span>
        </div>""", unsafe_allow_html=True)

    if not is_teacher:
        st.markdown("---")
        st.markdown(f"""
        <div style='background:{BG_GREEN};border-radius:12px;padding:16px;border:1px solid {MID_GREEN}'>
          <b style='color:{DARK_GREEN}'>ℹ️ Як переглянути свої оцінки?</b><br>
          <span style='color:{MID_GREEN};font-size:13px'>
            Перейдіть на вкладку <b>Аналітика</b>. Якщо ваше ім'я є в базі —
            ви побачите свої оцінки та позицію в рейтингу.
            Якщо оцінок немає — попросіть викладача прив'язати ваш акаунт.
          </span>
        </div>""", unsafe_allow_html=True)

elif "Завантаження" in page:
    upload.show()

elif "Аналітика" in page:
    analytics.show(is_teacher, user_name)

elif "Прогнози" in page:
    forecasting_page.show()

elif "Експорт" in page:
    export_page.show()

elif "Користувачі" in page:
    users_page.show()

elif "Синхронізація" in page:
    sync_page.show()