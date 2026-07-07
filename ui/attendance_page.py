# ui/attendance_page.py

import streamlit as st

from services.attendance_service import (
    save_check_in,
    save_check_out,
    attendance_exists_today,
    has_checked_out_today
)


def render_attendance_page():

    st.title(
        "🕒 الحضور والانصراف"
    )

    employee_name = (
        st.session_state.display_name
    )

    checked_in = (
        attendance_exists_today(
            employee_name
        )
    )

    checked_out = (
        has_checked_out_today(
            employee_name
        )
    )

    # -------------------
    # No Check In Yet
    # -------------------

    if not checked_in:

        st.info(
            "قم بتسجيل الحضور"
        )

        if st.button(
            "🟢 Check In"
        ):

            save_check_in(
                employee_name
            )

            st.success(
                "تم تسجيل الحضور"
            )

            st.rerun()

        return

    # -------------------
    # Check In Done
    # -------------------

    if (
        checked_in
        and
        not checked_out
    ):

        st.success(
            "✅ تم تسجيل الحضور"
        )

        if st.button(
            "🔴 Check Out"
        ):

            save_check_out(
                employee_name
            )

            st.success(
                "تم تسجيل الانصراف"
            )

            st.rerun()

        return

    # -------------------
    # Finished
    # -------------------

    st.success(
        "✅ تم تسجيل الحضور والانصراف اليوم"
    )