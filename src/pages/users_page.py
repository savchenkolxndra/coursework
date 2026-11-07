"""
pages/users_page.py — управління користувачами (тільки для викладача/адміна)
"""
import streamlit as st
from database import list_users, delete_user, register_user, link_student_user, load_grades
from config import DARK_GREEN, BG_GREEN, MID_GREEN, GOLD_LIGHT, GOLD_MID, GOLD


def show() -> None:
    st.title("👥 Управління користувачами")

    tab1, tab2, tab3 = st.tabs(["📋 Список", "➕ Додати", "🔗 Прив'язати студента"])

    with tab1:
        df = list_users()
        if df.empty:
            st.info("Користувачів немає.")
        else:
            role_map = {"teacher": "Викладач", "student": "Студент"}
            df["role"] = df["role"].map(role_map)
            df = df.rename(columns={
                "id": "ID", "username": "Логін", "role": "Роль",
                "full_name": "Повне ім'я", "created_at": "Дата реєстрації"
            })
            st.dataframe(df, hide_index=True, use_container_width=True)

            st.subheader("Видалити користувача")
            users_raw = list_users()
            non_admin = users_raw[users_raw["username"] != "admin"]
            if not non_admin.empty:
                opts = {f"{r['full_name']} ({r['username']})": r["id"]
                        for _, r in non_admin.iterrows()}
                selected = st.selectbox("Оберіть користувача", list(opts.keys()), key="del_user")
                if st.button("🗑️ Видалити", key="btn_del_user"):
                    delete_user(opts[selected])
                    st.success("Видалено")
                    st.rerun()

    with tab2:
        st.markdown(f"""
        <div style='background:{BG_GREEN};border-radius:10px;padding:14px;
                    border:1px solid {MID_GREEN};margin-bottom:16px'>
          <b style='color:{DARK_GREEN}'>Додати нового викладача або студента</b>
        </div>""", unsafe_allow_html=True)

        c1, c2 = st.columns(2)
        with c1:
            new_name = st.text_input("Повне ім'я", key="new_name",
                                     placeholder="Іваненко Олена Петрівна")
            new_user = st.text_input("Логін", key="new_user", placeholder="ivanenko_o")
        with c2:
            new_pwd  = st.text_input("Пароль", type="password", key="new_pwd")
            new_role = st.selectbox("Роль", ["student", "teacher"],
                                    format_func=lambda x: "Студент" if x == "student" else "Викладач",
                                    key="new_role")

        if st.button("Створити користувача", use_container_width=True, key="btn_create"):
            if not all([new_name, new_user, new_pwd]):
                st.error("Заповніть всі поля")
            elif len(new_pwd) < 6:
                st.error("Пароль мінімум 6 символів")
            else:
                ok, msg = register_user(new_user, new_pwd, new_role, new_name)
                st.success(f"✅ {msg}") if ok else st.error(msg)

    with tab3:
        st.markdown("""
        Прив'язка дозволяє студенту бачити **свої** оцінки після входу.
        Ім'я в системі має точно збігатися з ім'ям у таблиці оцінок.
        """)

        grades_df = load_grades()
        users_df  = list_users()

        if grades_df.empty:
            st.info("Спочатку завантажте оцінки.")
            return

        students_in_grades = sorted(grades_df["student_name"].unique().tolist())
        student_users = users_df[users_df["role"] == "student"]

        if student_users.empty:
            st.info("Немає зареєстрованих студентів.")
            return

        c1, c2 = st.columns(2)
        with c1:
            sel_student_name = st.selectbox("Ім'я в таблиці оцінок", students_in_grades, key="link_sname")
        with c2:
            opts = {f"{r['full_name']} ({r['username']})": r["id"]
                    for _, r in student_users.iterrows()}
            sel_user_label = st.selectbox("Обліковий запис студента", list(opts.keys()), key="link_uname")

        if st.button("🔗 Прив'язати", use_container_width=True, key="btn_link"):
            ok = link_student_user(sel_student_name, opts[sel_user_label])
            st.success("✅ Прив'язано!") if ok else st.error("Помилка прив'язки")