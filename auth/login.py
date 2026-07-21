# auth/login.py

import time

import streamlit as st
from auth.users import USERS
from auth.cookie_manager import set_auth_cookie


def login_page():

    st.title("🔐 Login")

    username = st.text_input("Username")
    password = st.text_input(
        "Password",
        type="password"
    )

    if st.button("Login"):

        user = USERS.get(username)

        if (
            user
            and
            user["password"] == password
        ):

            st.session_state.logged_in = True

            st.session_state.username = username

            st.session_state.role = user["role"]

            st.session_state.display_name = (
                user["display_name"]
            )

            # الإضافة الجديدة: نخزن نفس البيانات فى كوكي
            # عشان تفضل موجودة حتى بعد refresh أو قفل المتصفح
            set_auth_cookie(
                username=username,
                role=user["role"],
                display_name=user["display_name"]
            )

            # تأخير بسيط لازم عشان الكومبوننت ياخد وقت كافي
            # ينفذ الـ JavaScript بتاعه ويحط الكوكي فعليًا فى
            # المتصفح قبل ما نعمل rerun ونغيّر الصفحة
            time.sleep(0.2)

            st.rerun()

        else:

            st.error(
                "Invalid username or password"
            )