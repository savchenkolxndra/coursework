"""
pages/sync_page.py — сторінка синхронізації з PostgreSQL
"""
import streamlit as st

from database import is_remote_available, sync_to_remote, count_unsynced, load_grades, clear_grades


def show() -> None:
    st.title("🔄 Синхронізація з PostgreSQL")

    online   = is_remote_available()
    unsynced = count_unsynced()
    total    = len(load_grades())

    c1, c2, c3 = st.columns(3)
    c1.metric("📡 Сервер",             "Доступний ✅" if online else "Недоступний ❌")
    c2.metric("🔄 Не синхронізовано",  unsynced)
    c3.metric("📋 Всього записів",      total)

    st.markdown("---")

    if online:
        st.success("Сервер доступний. Можна виконати синхронізацію.")
        if st.button("🔄 Синхронізувати зараз", use_container_width=True):
            with st.spinner("Відправляємо дані..."):
                ok, msg = sync_to_remote()
            if ok:
                st.success(f"✅ {msg}")
            else:
                st.warning(f"⚠️ {msg}")
    else:
        st.error("Сервер недоступний. Дані зберігаються локально.")
        st.markdown("""
        **Офлайн-режим:**
        - Всі дані зберігаються у локальному SQLite файлі
        - Нові записи позначені як «не синхронізовані»
        - Щойно з'явиться з'єднання — натисни «Синхронізувати зараз»
        """)

    st.markdown("---")
    st.subheader("🗑️ Очистити локальні дані")
    if st.checkbox("Підтверджую видалення всіх локальних даних"):
        if st.button("Видалити", use_container_width=True):
            clear_grades()
            st.success("✅ База очищена")
            st.rerun()