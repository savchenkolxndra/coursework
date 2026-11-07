"""
pages/forecasting_page.py — сторінка прогнозів успішності
"""
import streamlit as st
from database import load_grades
from forecasting import (
    forecast_overall_linear,
    forecast_overall_poly,
    forecast_by_group,
    forecast_student,
)


def show() -> None:
    st.title("🔮 Прогнози успішності")

    df = load_grades()
    if df.empty:
        st.info("Завантажте дані щоб побачити прогнози.")
        return

    n_future = st.slider("Кількість майбутніх періодів для прогнозу", 1, 6, 3)
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Лінійний тренд",
        "〰️ Поліноміальна регресія",
        "👥 По групах",
        "👤 Конкретний студент",
    ])

    with tab1:
        forecast_overall_linear(df, n_future)

    with tab2:
        degree = st.radio("Степінь полінома", [2, 3], horizontal=True, key="poly_deg")
        forecast_overall_poly(df, n_future, degree)

    with tab3:
        forecast_by_group(df, n_future)

    with tab4:
        forecast_student(df, n_future)