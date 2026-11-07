"""
pages/analytics.py — сторінка аналітики з графіками
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import (
    CHART_COLORS, SCALE_GRADE, AMBER, RED, GREEN_CHART as GREEN,
    DARK_GREEN, MID_GREEN, LIGHT_GREEN, BG_GREEN, PALE_GREEN,
    GOLD, GOLD_LIGHT, GOLD_MID,
)
# Аліаси для сумісності з графіками
PINK1 = GOLD
PINK2 = GOLD_LIGHT
PINK3 = GOLD_MID
VIO1  = MID_GREEN
VIO2  = DARK_GREEN
from database import load_grades as load_all_data

BINS   = [0, 60, 75, 90, 100]
LABELS = ["Незадовільно", "Задовільно", "Добре", "Відмінно"]
ORDER  = ["Відмінно", "Добре", "Задовільно", "Незадовільно"]
PIE_COLORS = [GREEN, VIO1, AMBER, RED]


def show(is_teacher: bool, user_name: str) -> None:
    st.title("📈 Аналітика")

    df_all = load_all_data()
    if df_all.empty:
        st.info("Дані ще не завантажені.")
        return

    df_full = df_all.copy()  # для рейтингу — завжди всі студенти

    if not is_teacher:
        df_all = df_all[df_all["student_name"].str.contains(user_name, case=False, na=False)]
        if df_all.empty:
            st.warning(f"Записів для «{user_name}» не знайдено.")
            return

    # ── Фільтри ──────────────────────────────────────────────────────────────
    with st.expander("🔎 Фільтри", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            sel_g = st.multiselect(
                "Групи",
                ["Усі"] + sorted(df_all["group_name"].unique().tolist()),
                default=["Усі"]
            )
        with c2:
            sel_t = st.multiselect(
                "Теми",
                ["Усі"] + sorted(df_all["topic"].unique().tolist()),
                default=["Усі"]
            )
        with c3:
            if not df_all["upload_date"].empty:
                mn = df_all["upload_date"].min().date()
                mx = df_all["upload_date"].max().date()
                dr = st.date_input("Період", (mn, mx), min_value=mn, max_value=mx)
            else:
                dr = ()

    df = df_all.copy()
    if "Усі" not in sel_g:
        df = df[df["group_name"].isin(sel_g)]
    if "Усі" not in sel_t:
        df = df[df["topic"].isin(sel_t)]
    if len(dr) == 2:
        df = df[
            (df["upload_date"].dt.date >= dr[0]) &
            (df["upload_date"].dt.date <= dr[1])
        ]

    if df.empty:
        st.warning("Немає даних за фільтрами.")
        return

    df["grade_level"] = pd.cut(df["grade"], bins=BINS, labels=LABELS, include_lowest=True)

    # ── Метрики ───────────────────────────────────────────────────────────────
    _show_metrics(df, is_teacher, user_name)
    st.markdown("---")

    # ── Вкладки ───────────────────────────────────────────────────────────────
    if is_teacher:
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "📊 Групи і теми", "🍩 Розподіл", "🔥 Heatmap",
            "🏅 Рейтинг", "📦 Розкид балів", "📅 Динаміка"
        ])
        _tab_groups_topics(tab1, df)
        _tab_distribution(tab2, df)
        _tab_heatmap(tab3, df)
        _tab_rating(tab4, df, df_full, is_teacher, user_name)
        _tab_boxplot(tab5, df)
        _tab_dynamics(tab6, df)
    else:
        tab1, tab2, tab4 = st.tabs(["📊 Групи і теми", "🍩 Розподіл", "🏅 Рейтинг"])
        _tab_groups_topics(tab1, df)
        _tab_distribution(tab2, df)
        _tab_rating(tab4, df, df_full, is_teacher, user_name)

    # ── Таблиця ───────────────────────────────────────────────────────────────
    st.markdown("---")
    if is_teacher:
        st.subheader("Таблиця даних")
        st.dataframe(
            df[["group_name", "student_name", "topic", "grade", "upload_date"]],
            use_container_width=True
        )
    else:
        st.subheader("📋 Мої оцінки")
        my_df = df[df["student_name"].str.contains(user_name, case=False, na=False)]
        st.dataframe(
            my_df[["topic", "grade"]].rename(columns={"topic": "Предмет", "grade": "Оцінка"}),
            use_container_width=True, hide_index=True
        )


# ── Допоміжні функції ─────────────────────────────────────────────────────────

def _show_metrics(df, is_teacher, user_name):
    st.subheader("Основні показники")
    if is_teacher:
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        c1.metric("📋 Оцінок",      len(df))
        c2.metric("⭐ Середній",    f"{df['grade'].mean():.2f}")
        c3.metric("📊 Медіана",     f"{df['grade'].median():.1f}")
        c4.metric("📉 Мін",         f"{df['grade'].min():.0f}")
        c5.metric("📈 Макс",        f"{df['grade'].max():.0f}")
        c6.metric("🏆 Відмінники",  f"{(df['grade_level']=='Відмінно').sum()/len(df)*100:.0f}%")
    else:
        my_grades = df[df["student_name"].str.contains(user_name, case=False, na=False)]["grade"]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("📋 Оцінок у групі",         len(df))
        c2.metric("⭐ Середній по групі",       f"{df['grade'].mean():.2f}")
        if not my_grades.empty:
            c3.metric("🎯 Мій середній бал",   f"{my_grades.mean():.2f}")
            diff = my_grades.mean() - df["grade"].mean()
            c4.metric("📊 Відхилення від середнього", f"{diff:+.2f}")


def _tab_groups_topics(tab, df):
    with tab:
        cl, cr = st.columns(2)
        with cl:
            by_g = df.groupby("group_name")["grade"].mean().reset_index().sort_values("grade", ascending=False)
            fig = px.bar(by_g, x="group_name", y="grade", text_auto=".1f",
                         color="grade", color_continuous_scale=SCALE_GRADE,
                         labels={"group_name": "Група", "grade": "Середній бал"})
            fig.update_layout(title="Середній бал по групах", coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            by_t = df.groupby("topic")["grade"].mean().reset_index().sort_values("grade", ascending=False)
            fig = px.bar(by_t, x="topic", y="grade", text_auto=".1f",
                         color="grade", color_continuous_scale=SCALE_GRADE,
                         labels={"topic": "Тема", "grade": "Середній бал"})
            fig.update_layout(title="Середній бал по темах", coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        if df["topic"].nunique() > 1:
            pivot_bar = df.groupby(["group_name", "topic"])["grade"].mean().reset_index()
            fig = px.bar(pivot_bar, x="group_name", y="grade", color="topic",
                         barmode="group", text_auto=".1f",
                         color_discrete_sequence=CHART_COLORS,
                         labels={"group_name": "Група", "grade": "Середній бал", "topic": "Тема"})
            fig.update_layout(title="Середній бал по групах і темах разом")
            st.plotly_chart(fig, use_container_width=True)


def _tab_distribution(tab, df):
    with tab:
        cl, cr = st.columns(2)
        with cl:
            lc = df["grade_level"].value_counts().reindex(ORDER).reset_index()
            lc.columns = ["Рівень", "Кількість"]
            fig = px.pie(lc, values="Кількість", names="Рівень",
                         color="Рівень",
                         color_discrete_map=dict(zip(ORDER, PIE_COLORS)),
                         hole=0.42)
            fig.update_traces(textposition="inside", textinfo="percent+label", textfont_size=13)
            fig.update_layout(title="Розподіл за рівнями",
                              legend=dict(orientation="h", y=-0.15, x=0.5, xanchor="center"))
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            fig = px.histogram(df, x="grade", nbins=20,
                               color_discrete_sequence=[VIO1],
                               labels={"grade": "Бал", "count": "Кількість"})
            fig.add_vline(x=df["grade"].mean(), line_dash="dash", line_color=VIO2,
                          annotation_text=f"Середнє: {df['grade'].mean():.1f}")
            fig.update_layout(title="Гістограма балів")
            st.plotly_chart(fig, use_container_width=True)

        if df["group_name"].nunique() > 1:
            groups = df["group_name"].unique()
            gcols = st.columns(min(len(groups), 3))
            for i, grp in enumerate(groups):
                g_df = df[df["group_name"] == grp]
                lc_g = g_df["grade_level"].value_counts().reindex(ORDER).reset_index()
                lc_g.columns = ["Рівень", "Кількість"]
                fig = px.pie(lc_g, values="Кількість", names="Рівень",
                             color="Рівень",
                             color_discrete_map=dict(zip(ORDER, PIE_COLORS)),
                             hole=0.35)
                fig.update_traces(textinfo="percent", textfont_size=11)
                fig.update_layout(title=f"Група {grp}", showlegend=False,
                                  margin=dict(t=40, b=10, l=10, r=10))
                gcols[i % 3].plotly_chart(fig, use_container_width=True)


def _tab_heatmap(tab, df):
    with tab:
        pivot = df.pivot_table(
            values="grade", index="student_name",
            columns="topic", aggfunc="mean"
        )
        fig = px.imshow(pivot, text_auto=".1f",
                        color_continuous_scale=[[0, RED], [0.5, AMBER], [1, GREEN]],
                        aspect="auto")
        fig.update_layout(
            title="Теплова карта: студент × тема  (червоний = низький бал, зелений = високий)",
            xaxis_title="Тема", yaxis_title="Студент"
        )
        st.plotly_chart(fig, use_container_width=True)


def _tab_rating(tab, df, df_full, is_teacher, user_name):
    with tab:
        cl, cr = st.columns(2)
        with cl:
            top10 = df.groupby("student_name")["grade"].mean().nlargest(10).reset_index()
            fig = px.bar(top10, x="grade", y="student_name", orientation="h",
                         text_auto=".1f", color="grade",
                         color_continuous_scale=SCALE_GRADE,
                         labels={"student_name": "Студент", "grade": "Середній бал"})
            fig.update_layout(title="Топ-10 студентів", coloraxis_showscale=False,
                              yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            bot10 = df.groupby("student_name")["grade"].mean().nsmallest(10).reset_index()
            fig = px.bar(bot10, x="grade", y="student_name", orientation="h",
                         text_auto=".1f", color="grade",
                         color_continuous_scale=[[0, RED], [1, AMBER]],
                         labels={"student_name": "Студент", "grade": "Середній бал"})
            fig.update_layout(title="10 студентів з найнижчим балом",
                              coloraxis_showscale=False,
                              yaxis={"categoryorder": "total descending"})
            st.plotly_chart(fig, use_container_width=True)

        all_students = (
            df_full.groupby("student_name")["grade"]
            .mean()
            .reset_index()
            .sort_values("grade", ascending=False)
        )
        all_students["rank"]  = range(1, len(all_students) + 1)
        all_students["grade"] = all_students["grade"].round(2)

        st.subheader("Повний рейтинг студентів")
        st.dataframe(
            all_students.rename(columns={"rank": "Місце", "student_name": "Студент", "grade": "Середній бал"}),
            use_container_width=True, hide_index=True
        )
        if not is_teacher:
            my_row = all_students[
                all_students["student_name"].str.contains(user_name, case=False, na=False)
            ]
            if not my_row.empty:
                my_rank = int(my_row["rank"].iloc[0])
                my_avg  = float(my_row["grade"].iloc[0])
                total_s = len(all_students)
                st.markdown(f"""
                <div style='background:#E8F5E9;border-radius:12px;padding:16px;
                            border:1px solid #81C784;text-align:center;margin-top:12px'>
                  <span style='font-size:13px;color:#2E7D32'>Ваша позиція: </span>
                  <span style='font-size:22px;font-weight:700;color:#1B5E20'>#{my_rank}</span>
                  <span style='font-size:13px;color:#388E3C'>
                    &nbsp;з {total_s} · середній бал <b>{my_avg}</b>
                  </span>
                </div>
                """, unsafe_allow_html=True)


def _tab_boxplot(tab, df):
    with tab:
        st.markdown("""
        > **Box plot** — «ящик з вусами». Ящик = середні 50% студентів,
        лінія всередині = медіана, «вуса» = мін і макс.
        Вузький ящик → група рівна, широкий → великий розкид.
        """)
        cl, cr = st.columns(2)
        with cl:
            fig = px.box(df, x="group_name", y="grade", color="group_name",
                         color_discrete_sequence=CHART_COLORS, points="all",
                         labels={"group_name": "Група", "grade": "Бал"})
            fig.update_layout(title="Розкид балів по групах", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with cr:
            fig = px.box(df, x="topic", y="grade", color="topic",
                         color_discrete_sequence=CHART_COLORS, points="all",
                         labels={"topic": "Тема", "grade": "Бал"})
            fig.update_layout(title="Розкид балів по темах", showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        if df["topic"].nunique() > 1:
            st.markdown("""
            > **Кореляція між предметами** — чи пов'язані оцінки?
            Якщо хто добре з математики і також з програмування — висока кореляція (близько 1.0).
            """)
            pivot_c = df.pivot_table(
                values="grade", index="student_name", columns="topic", aggfunc="mean"
            )
            if pivot_c.shape[0] >= 3:
                corr = pivot_c.corr().round(2)
                fig = px.imshow(corr, text_auto=True,
                                color_continuous_scale=[[0, PINK3], [0.5, PINK2], [1, PINK1]],
                                zmin=-1, zmax=1)
                fig.update_layout(title="Кореляція між предметами (1.0 = повний зв'язок)")
                st.plotly_chart(fig, use_container_width=True)

        st.subheader("⚠️ Студенти нижче 60 балів")
        low = df[df["grade"] < 60][["group_name", "student_name", "topic", "grade"]].sort_values("grade")
        if low.empty:
            st.success("Студентів нижче 60 балів немає 🎉")
        else:
            st.dataframe(low, use_container_width=True)


def _tab_dynamics(tab, df):
    with tab:
        st.markdown("Динаміка показує як змінювався середній бал по датах завантаження файлів.")
        df = df.copy()
        df["date"] = df["upload_date"].dt.date
        by_date = df.groupby("date")["grade"].mean().reset_index()
        by_date.columns = ["Дата", "Середній бал"]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=by_date["Дата"], y=by_date["Середній бал"],
            mode="lines+markers+text",
            text=by_date["Середній бал"].round(1),
            textposition="top center",
            line=dict(color=PINK1, width=3),
            marker=dict(color=VIO2, size=10)
        ))
        fig.update_layout(title="Середній бал по датах завантаження",
                          xaxis_title="Дата", yaxis_title="Середній бал")
        st.plotly_chart(fig, use_container_width=True)

        if df["group_name"].nunique() > 1:
            by_date_g = df.groupby(["date", "group_name"])["grade"].mean().reset_index()
            fig = px.line(by_date_g, x="date", y="grade", color="group_name",
                          markers=True, color_discrete_sequence=CHART_COLORS,
                          labels={"date": "Дата", "grade": "Середній бал", "group_name": "Група"})
            fig.update_layout(title="Динаміка по групах")
            st.plotly_chart(fig, use_container_width=True)