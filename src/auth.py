"""
auth.py — авторизація та реєстрація користувачів.
Паролі зберігаються як SHA-256 хеш, не у відкритому вигляді.
"""
import streamlit as st

from config import CUSTOM_CSS, DARK_GREEN, MID_GREEN, BG_GREEN, GOLD, GOLD_LIGHT, GOLD_MID
from database import authenticate, register_user


def show_login() -> None:
    """Показує форму входу та реєстрації."""
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1])

    # ── Вхід ──────────────────────────────────────────────────────────────────
    with col_l:
        st.markdown(f"""
        <div style='background:{BG_GREEN};border-radius:14px;padding:24px;
                    border:1px solid {MID_GREEN};margin-bottom:8px'>
          <h3 style='color:{DARK_GREEN};margin:0 0 4px'>🔐 Вхід до системи</h3>
          <p style='color:{MID_GREEN};font-size:12px;margin:0'>
            Для викладачів і студентів
          </p>
        </div>""", unsafe_allow_html=True)

        login_username = st.text_input("Логін", key="login_u", placeholder="your_login")
        login_password = st.text_input("Пароль", type="password", key="login_p")

        if st.button("Увійти →", use_container_width=True, key="btn_login"):
            if not login_username or not login_password:
                st.error("Введіть логін і пароль")
            else:
                user = authenticate(login_username, login_password)
                if user:
                    st.session_state.update({
                        "logged_in": True,
                        "user_id":   user["id"],
                        "role":      user["role"],
                        "username":  user["username"],
                        "full_name": user["full_name"],
                    })
                    st.rerun()
                else:
                    st.error("Невірний логін або пароль")

    # ── Реєстрація ────────────────────────────────────────────────────────────
    with col_r:
        st.markdown(f"""
        <div style='background:{GOLD_LIGHT};border-radius:14px;padding:24px;
                    border:1px solid {GOLD_MID};margin-bottom:8px'>
          <h3 style='color:{GOLD};margin:0 0 4px'>📝 Реєстрація</h3>
          <p style='color:#666;font-size:12px;margin:0'>
            Нові викладачі та студенти
          </p>
        </div>""", unsafe_allow_html=True)

        reg_name     = st.text_input("Повне ім'я", key="reg_name",
                                     placeholder="Іваненко Олена Петрівна")
        reg_username = st.text_input("Логін", key="reg_u", placeholder="ivanenko_o")
        reg_password = st.text_input("Пароль", type="password", key="reg_p")
        reg_role     = st.selectbox("Роль", ["student", "teacher"],
                                    format_func=lambda x: "Студент" if x == "student" else "Викладач",
                                    key="reg_role")

        if st.button("Зареєструватись", use_container_width=True, key="btn_reg"):
            if not all([reg_name, reg_username, reg_password]):
                st.error("Заповніть всі поля")
            elif len(reg_password) < 6:
                st.error("Пароль мінімум 6 символів")
            else:
                ok, msg = register_user(reg_username, reg_password, reg_role, reg_name)
                if ok:
                    st.success(f"✅ {msg}. Тепер увійдіть зліва.")
                else:
                    st.error(msg)