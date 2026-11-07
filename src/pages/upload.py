"""
pages/upload.py — сторінка завантаження даних з вибором дати
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta

from database import save_grades

RENAME_MAP = {
    "група": "group_name", "груп": "group_name", "group": "group_name", "Група": "group_name",
    "студент": "student_name", "піб": "student_name", "Студент": "student_name",
    "тема": "topic", "предмет": "topic", "Тема": "topic", "Topic": "topic", "subject": "topic",
    "оцінка": "grade", "бал": "grade", "Оцінка": "grade", "Grade": "grade",
    "Бал": "grade", "score": "grade",
}
REQUIRED = ["group_name", "student_name", "topic", "grade"]


def show() -> None:
    st.title("📤 Завантаження даних")

    # ── Вибір дати ──────────────────────────────────────────────────────────
    st.subheader("📅 Дата завантаження")
    st.markdown("Можна вказати будь-яку дату — це дозволить бачити динаміку на графіках прогнозів.")

    col1, col2 = st.columns([2, 3])
    with col1:
        use_custom = st.checkbox("Вказати дату вручну", value=False)
    with col2:
        if use_custom:
            upload_date = st.date_input(
                "Дата",
                value=date.today(),
                min_value=date(2020, 1, 1),
                max_value=date.today()
            )
        else:
            upload_date = date.today()
            st.markdown(f"<span style='color:#2E7D32'>Використовується сьогоднішня дата: **{upload_date}**</span>",
                        unsafe_allow_html=True)

    st.markdown("---")

    # ── Завантаження файлу ───────────────────────────────────────────────────
    uploaded = st.file_uploader("CSV або XLSX з оцінками", type=["csv", "xlsx"])
    if not uploaded:
        return

    try:
        df = (
            pd.read_csv(uploaded)
            if uploaded.name.endswith(".csv")
            else pd.read_excel(uploaded)
        )
        df.columns = df.columns.str.strip().str.lower()
        df = df.rename(columns=RENAME_MAP)

        missing = [c for c in REQUIRED if c not in df.columns]
        if missing:
            st.error(f"Не знайдено колонок: {', '.join(missing)}")
            return

        df = df[REQUIRED].copy()
        df["grade"] = pd.to_numeric(df["grade"], errors="coerce")
        df = df.dropna(subset=["grade"])

        # Передаємо вибрану дату
        count = save_grades(df, upload_date=str(upload_date))
        st.success(f"✅ Збережено **{count}** оцінок з датою **{upload_date}**")
        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Помилка обробки файлу: {e}")