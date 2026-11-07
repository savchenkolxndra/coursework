"""
pages/export_page.py — сторінка експорту звітів
"""
import streamlit as st

from config import DARK_GREEN, MID_GREEN, BG_GREEN, LIGHT_GREEN, GOLD, GOLD_LIGHT, GOLD_MID
VIO2, VIO3, VIO4, VIO1 = DARK_GREEN, BG_GREEN, LIGHT_GREEN, MID_GREEN
PINK1, PINK3, PINK4    = GOLD, GOLD_LIGHT, GOLD_MID
from database import load_grades as load_all_data
from export import export_pdf, export_excel, export_csv


def show() -> None:
    st.title("📥 Експорт звітів")

    df = load_all_data()
    if df.empty:
        st.info("Немає даних для експорту.")
        return

    st.markdown(f"В базі **{len(df)}** записів. Оберіть формат:")
    c1, c2, c3 = st.columns(3)

    with c1:
        st.markdown(f"""
        <div style='background:{VIO3};border-radius:12px;padding:14px;
                    border:1px solid {VIO4};margin-bottom:10px'>
          <b style='color:{VIO2}'>📄 PDF звіт</b><br>
          <span style='color:{VIO1};font-size:12px'>Таблиці статистики з кирилицею</span>
        </div>""", unsafe_allow_html=True)
        try:
            st.download_button(
                "⬇️ Завантажити PDF",
                data=export_pdf(df),
                file_name="grades_report.pdf",
                mime="application/pdf",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Помилка PDF: {e}")

    with c2:
        st.markdown(f"""
        <div style='background:{PINK3};border-radius:12px;padding:14px;
                    border:1px solid {PINK4};margin-bottom:10px'>
          <b style='color:{PINK1}'>📊 Excel (XLSX)</b><br>
          <span style='color:{PINK1};font-size:12px'>3 аркуші: оцінки, групи, теми</span>
        </div>""", unsafe_allow_html=True)
        st.download_button(
            "⬇️ Завантажити Excel",
            data=export_excel(df),
            file_name="grades_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with c3:
        st.markdown("""
        <div style='background:#E1F5EE;border-radius:12px;padding:14px;
                    border:1px solid #5DCAA5;margin-bottom:10px'>
          <b style='color:#0F6E56'>📝 CSV</b><br>
          <span style='color:#085041;font-size:12px'>Для будь-якого інструменту аналізу</span>
        </div>""", unsafe_allow_html=True)
        st.download_button(
            "⬇️ Завантажити CSV",
            data=export_csv(df),
            file_name="grades_report.csv",
            mime="text/csv",
            use_container_width=True
        )