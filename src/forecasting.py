"""
forecasting.py — прогнози успішності на основі регресійних моделей.

Методи:
  1. Лінійна регресія тренду (group або student)
  2. Поліноміальна регресія (degree=2)
  3. Прогноз середнього балу групи на наступний період
  4. Прогноз для конкретного студента
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import streamlit as st
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.metrics import r2_score

from config import DARK_GREEN, MID_GREEN, GOLD, AMBER, RED, CHART_COLORS


# ── Утиліти ───────────────────────────────────────────────────────────────────

def _df_to_time_series(df: pd.DataFrame, group_col: str | None = None) -> pd.DataFrame:
    """
    Перетворює датафрейм на часовий ряд:
    впорядковані унікальні дати → числові індекси (0,1,2,...).
    """
    df = df.copy()
    df["date"] = pd.to_datetime(df["upload_date"]).dt.date
    if group_col:
        ts = df.groupby([group_col, "date"])["grade"].mean().reset_index()
        ts = ts.sort_values([group_col, "date"])
        ts["t"] = ts.groupby(group_col).cumcount()
    else:
        ts = df.groupby("date")["grade"].mean().reset_index().sort_values("date")
        ts["t"] = range(len(ts))
    return ts


def _fit_linear(X: np.ndarray, y: np.ndarray):
    model = LinearRegression().fit(X, y)
    return model, r2_score(y, model.predict(X))


def _fit_poly(X: np.ndarray, y: np.ndarray, degree: int = 2):
    model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
    model.fit(X, y)
    return model, r2_score(y, model.predict(X))


# ── 1. Лінійний тренд загального середнього ───────────────────────────────────

def forecast_overall_linear(df: pd.DataFrame, n_future: int = 3) -> None:
    """Лінійний тренд загального середнього балу + прогноз на n_future точок."""
    st.markdown("""
    > **Лінійна регресія** — проводить пряму лінію через наявні дані і продовжує її вперед.
    Якщо середній бал поступово зростає або падає — регресія покаже цей тренд.
    """)

    ts = _df_to_time_series(df)
    if len(ts) < 2:
        st.info("Для прогнозу потрібно мінімум 2 точки в часі (2 завантаження з різними датами).")
        return

    X = ts["t"].values.reshape(-1, 1)
    y = ts["grade"].values
    model, r2 = _fit_linear(X, y)

    t_future = np.arange(len(ts), len(ts) + n_future).reshape(-1, 1)
    y_pred_hist   = model.predict(X)
    y_pred_future = model.predict(t_future)
    future_dates  = [f"Прогноз +{i+1}" for i in range(n_future)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts["date"].astype(str), y=y,
        mode="lines+markers", name="Фактичні дані",
        line=dict(color=DARK_GREEN, width=2),
        marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=ts["date"].astype(str), y=y_pred_hist,
        mode="lines", name="Тренд (лінійна регресія)",
        line=dict(color=GOLD, width=2, dash="dot")
    ))
    fig.add_trace(go.Scatter(
        x=future_dates, y=y_pred_future,
        mode="lines+markers", name="Прогноз",
        line=dict(color=AMBER, width=2, dash="dash"),
        marker=dict(symbol="diamond", size=10)
    ))
    fig.update_layout(
        title=f"Лінійний тренд середнього балу  |  R² = {r2:.3f}",
        xaxis_title="Дата / Період", yaxis_title="Середній бал",
        legend=dict(orientation="h", y=-0.2)
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("R² (точність моделі)", f"{r2:.3f}",
                help="1.0 = ідеальне передбачення, 0 = не краще за середнє")
    col2.metric("Нахил тренду",
                f"{model.coef_[0]:.3f} балів/період",
                delta="зростає ↑" if model.coef_[0] > 0 else "спадає ↓")
    col3.metric(f"Прогноз через {n_future} період(и)",
                f"{y_pred_future[-1]:.1f}")


# ── 2. Поліноміальна регресія ─────────────────────────────────────────────────

def forecast_overall_poly(df: pd.DataFrame, n_future: int = 3, degree: int = 2) -> None:
    """Поліноміальна регресія степеня degree + прогноз."""
    st.markdown(f"""
    > **Поліноміальна регресія (степінь {degree})** — гнучкіша крива ніж пряма лінія.
    Краще вловлює нелінійні тенденції, наприклад: спочатку ріст, потім стабілізація.
    """)

    ts = _df_to_time_series(df)
    if len(ts) < 3:
        st.info("Для поліноміальної регресії потрібно мінімум 3 точки.")
        return

    X = ts["t"].values.reshape(-1, 1)
    y = ts["grade"].values
    model, r2 = _fit_poly(X, y, degree)

    t_future      = np.arange(len(ts), len(ts) + n_future).reshape(-1, 1)
    y_pred_hist   = model.predict(X)
    y_pred_future = model.predict(t_future)
    future_dates  = [f"Прогноз +{i+1}" for i in range(n_future)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts["date"].astype(str), y=y,
        mode="lines+markers", name="Фактичні дані",
        line=dict(color=DARK_GREEN, width=2), marker=dict(size=8)
    ))
    fig.add_trace(go.Scatter(
        x=ts["date"].astype(str), y=y_pred_hist,
        mode="lines", name=f"Полін. регресія (степінь {degree})",
        line=dict(color=GOLD, width=2, dash="dot")
    ))
    fig.add_trace(go.Scatter(
        x=future_dates, y=y_pred_future,
        mode="lines+markers", name="Прогноз",
        line=dict(color=AMBER, width=2, dash="dash"),
        marker=dict(symbol="diamond", size=10)
    ))
    fig.update_layout(
        title=f"Поліноміальна регресія (степінь {degree})  |  R² = {r2:.3f}",
        xaxis_title="Дата / Період", yaxis_title="Середній бал",
        legend=dict(orientation="h", y=-0.2)
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    col1.metric("R²", f"{r2:.3f}")
    col2.metric(f"Прогноз через {n_future} пер.", f"{y_pred_future[-1]:.1f}")


# ── 3. Прогноз по групах ──────────────────────────────────────────────────────

def forecast_by_group(df: pd.DataFrame, n_future: int = 3) -> None:
    """Лінійний тренд + прогноз для кожної групи окремо."""
    st.markdown("""
    > Порівняння трендів між групами — видно яка група прогресує,
    а яка потребує уваги викладача.
    """)

    ts = _df_to_time_series(df, group_col="group_name")
    groups = ts["group_name"].unique()

    if len(ts) < 2:
        st.info("Потрібно мінімум 2 дати завантаження.")
        return

    fig = go.Figure()
    forecast_summary = []

    for i, grp in enumerate(groups):
        g = ts[ts["group_name"] == grp].sort_values("t")
        if len(g) < 2:
            continue
        X = g["t"].values.reshape(-1, 1)
        y = g["grade"].values
        model, r2 = _fit_linear(X, y)

        t_max    = int(g["t"].max())
        t_future = np.arange(t_max + 1, t_max + n_future + 1).reshape(-1, 1)
        y_future = model.predict(t_future)

        color = CHART_COLORS[i % len(CHART_COLORS)]
        dates_str = g["date"].astype(str).tolist()
        future_labels = [f"{grp} +{j+1}" for j in range(n_future)]

        fig.add_trace(go.Scatter(
            x=dates_str, y=y,
            mode="lines+markers", name=f"{grp} (факт)",
            line=dict(color=color, width=2), marker=dict(size=7)
        ))
        fig.add_trace(go.Scatter(
            x=future_labels, y=y_future,
            mode="lines+markers", name=f"{grp} (прогноз)",
            line=dict(color=color, width=2, dash="dash"),
            marker=dict(symbol="diamond", size=9)
        ))
        forecast_summary.append({
            "Група": grp,
            "Поточний сер. бал": round(float(y[-1]), 2),
            f"Прогноз через {n_future} пер.": round(float(y_future[-1]), 2),
            "Тренд": f"{'↑' if model.coef_[0] > 0 else '↓'} {model.coef_[0]:.3f}/пер.",
            "R²": round(r2, 3),
        })

    fig.update_layout(
        title="Прогноз середнього балу по групах",
        xaxis_title="Дата / Період", yaxis_title="Середній бал",
        legend=dict(orientation="h", y=-0.25)
    )
    st.plotly_chart(fig, use_container_width=True)

    if forecast_summary:
        st.subheader("Зведена таблиця прогнозів")
        st.dataframe(pd.DataFrame(forecast_summary), hide_index=True, use_container_width=True)


# ── 4. Прогноз для конкретного студента ───────────────────────────────────────

def forecast_student(df: pd.DataFrame, n_future: int = 3) -> None:
    """Лінійний тренд для обраного студента + поліноміальний."""
    students = sorted(df["student_name"].unique().tolist())
    if not students:
        st.info("Немає даних.")
        return

    selected = st.selectbox("Оберіть студента", students, key="fc_student")
    s_df = df[df["student_name"] == selected].copy()

    ts = _df_to_time_series(s_df)
    if len(ts) < 2:
        st.info("Для цього студента недостатньо точок у часі.")
        return

    X = ts["t"].values.reshape(-1, 1)
    y = ts["grade"].values
    lin_model, lin_r2 = _fit_linear(X, y)

    t_future      = np.arange(len(ts), len(ts) + n_future).reshape(-1, 1)
    y_lin_hist    = lin_model.predict(X)
    y_lin_future  = lin_model.predict(t_future)
    future_labels = [f"Прогноз +{j+1}" for j in range(n_future)]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ts["date"].astype(str), y=y,
        mode="lines+markers", name="Фактичні оцінки",
        line=dict(color=DARK_GREEN, width=2), marker=dict(size=9)
    ))
    fig.add_trace(go.Scatter(
        x=ts["date"].astype(str), y=y_lin_hist,
        mode="lines", name="Лінійний тренд",
        line=dict(color=GOLD, width=2, dash="dot")
    ))
    fig.add_trace(go.Scatter(
        x=future_labels, y=y_lin_future,
        mode="lines+markers", name="Прогноз (лінійний)",
        line=dict(color=AMBER, width=2, dash="dash"),
        marker=dict(symbol="diamond", size=10)
    ))

    # Поліноміальний якщо достатньо точок
    if len(ts) >= 3:
        poly_model, poly_r2 = _fit_poly(X, y, degree=2)
        y_poly_hist   = poly_model.predict(X)
        y_poly_future = poly_model.predict(t_future)
        fig.add_trace(go.Scatter(
            x=ts["date"].astype(str), y=y_poly_hist,
            mode="lines", name="Поліном. тренд (ступінь 2)",
            line=dict(color=MID_GREEN, width=2, dash="longdash")
        ))
        fig.add_trace(go.Scatter(
            x=future_labels, y=y_poly_future,
            mode="markers", name="Прогноз (поліном.)",
            marker=dict(symbol="star", size=12, color=MID_GREEN)
        ))

    fig.update_layout(
        title=f"Прогноз успішності: {selected}",
        xaxis_title="Дата / Період", yaxis_title="Середній бал",
        legend=dict(orientation="h", y=-0.25)
    )
    st.plotly_chart(fig, use_container_width=True)

    # Метрики
    trend_word = "зростає ↑" if lin_model.coef_[0] > 0 else "спадає ↓"
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Поточний середній", f"{y.mean():.2f}")
    c2.metric("Тренд",             f"{lin_model.coef_[0]:.3f} / пер.", delta=trend_word)
    c3.metric("R² (лінійний)",     f"{lin_r2:.3f}")
    c4.metric(f"Прогноз +{n_future}", f"{y_lin_future[-1]:.1f}")

    # Оцінки по предметах
    st.subheader(f"Оцінки по предметах — {selected}")
    by_subj = s_df.groupby("topic")["grade"].agg(["mean","min","max","count"]).round(2).reset_index()
    by_subj.columns = ["Предмет","Середнє","Мін","Макс","Кількість"]
    st.dataframe(by_subj, hide_index=True, use_container_width=True)


# Імпорт для використання у pages/forecasting_page.py
MID_GREEN = "#2E7D32"