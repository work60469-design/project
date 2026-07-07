# auth/login.py

import streamlit as st
from auth.users import USERS


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

            st.rerun()

        else:

            st.error(
                "Invalid username or password"
            )