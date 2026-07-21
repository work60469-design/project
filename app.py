# app.py

import streamlit as st

import os
import time

os.environ["TZ"] = "Africa/Cairo"

from auth.login import login_page
from auth.cookie_manager import (
    get_auth_data_from_cookie,
    clear_auth_cookie
)
from ui.home_page import render_home_page
from ui.student_page import render_student_page
from ui.edit_student_page import render_edit_student_page
from ui.leave_page import render_leave_page
from ui.feedback_page import render_feedback_page
from ui.dashboard_page import render_dashboard_page
from ui.report_dashboard_page import (
    render_report_dashboard
)
from ui.attendance_page import (
    render_attendance_page
)
from ui.break_page import (
    render_break_page
)
from ui.complaints_page import (
    render_complaints_page
)
from ui.data_review_page import (
    render_data_review_page
)
from services.daily_closure_service import (
    run_daily_closure_if_needed
)

# تهيئة إعدادات الصفحة
st.set_page_config(
    page_title="Biology Management",
    page_icon="🎓",
    layout="wide"
)

# ---------------------
# Session
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None

if "display_name" not in st.session_state:
    st.session_state.display_name = None

# لو مش مسجل دخول فى الـ session الحالية، نحاول نسترجع
# بياناته من الكوكي (يعنى كان مسجل دخول قبل كده ولسه صالحة)
if not st.session_state.logged_in:

    auth_data = get_auth_data_from_cookie()

    if auth_data:
        st.session_state.logged_in = True
        st.session_state.username = auth_data["username"]
        st.session_state.role = auth_data["role"]
        st.session_state.display_name = (
            auth_data["display_name"]
        )

# ---------------------
# Login
# ---------------------
if not st.session_state.logged_in:
    login_page()
else:

    # يتأكد إن الأيام اللي فاتت مقفولة صح (غياب / لم يتم
    # الإرسال) قبل ما نعرض أي صفحة. بتشتغل مرة واحدة بس
    # فى اليوم لكل جلسة، فمش هتعمل أي حمل زيادة على الشيتات.
    run_daily_closure_if_needed()

    with st.sidebar:

        # ---------------------
        # تحسين شكل القائمة الجانبية بس (بدون أي تغيير فى المنطق)
        # ---------------------
        st.markdown(
            """
            <style>
            section[data-testid="stSidebar"] {
                background-color: #f7f9f8;
            }
            div[role="radiogroup"] > label {
                padding: 8px 12px;
                border-radius: 8px;
                margin-bottom: 4px;
                transition: background-color 0.15s ease-in-out;
            }
            div[role="radiogroup"] > label:hover {
                background-color: #e6f0ea;
            }
            </style>
            """,
            unsafe_allow_html=True
        )

        st.title("🎓 Biology Management")
        st.success(st.session_state.display_name)

        # 0. حالة خاصة: السوبر أدمن بيشوف 3 صفحات بس
        if st.session_state.role == "super_admin":

            pages = [
                "الرئيسية",
                "Dashboard",
                "Report"
            ]

        else:

            # 1. بناء قائمة الصفحات الأساسية لجميع المستخدمين
            pages = [
                "الرئيسية",
                "طلب إجازة",
                "بريك اليوم",
                "تسجيل حضور",
                "Feedback"
            ]

            # 1.1 صفحات تسجيل/تعديل الطالب خاصة بتيم الـ support
            # (+ محمد الأدمن) بس، زي الفيدباك الخاص بكل تيم
            if (
                st.session_state.role == "support"
                or st.session_state.username == "amal"
            ):
                pages.insert(1, "تعديل طالب")
                pages.insert(1, "تسجيل طالب")

            # 1.2 صفحة الشكاوى تظهر لكل الموظفين ماعدا تيم social
            if st.session_state.role != "social":
                pages.append("الشكاوى")

            # 2. إضافة صفحات الإدارة فقط إذا كان المستخدم هو محمد
            if st.session_state.username == "amal":
                pages.extend([
                    "Dashboard",
                    "Report"
                ])

            # 2.1 صفحة مراجعة البيانات تظهر لسارة بس
            if st.session_state.username == "sara":
                pages.append("مراجعة البيانات")

        # لو جاي من زرار "تعديل" فى صفحة الطالب، نغير الصفحة
        # المختارة قبل ما الـ radio يتعرض (لازم يحصل قبل إنشاءه)
        if st.session_state.get("go_to_edit_page"):
            st.session_state["page_radio"] = "تعديل طالب"
            st.session_state["go_to_edit_page"] = False

        # 3. تمرير القائمة الجاهزة إلى st.radio
        # ملحوظة: أضفنا key="page_radio" عشان نقدر نتحكم فى
        # الصفحة المختارة من زرار "تعديل" جوه صفحة الطالب
        page = st.radio(
            "القائمة",
            pages,
            key="page_radio"
        )

        # زر تسجيل الخروج
        if st.button("🚪 تسجيل الخروج"):
            clear_auth_cookie()
            st.session_state.logged_in = False
            st.rerun()

    # ---------------------
    # توجيه الصفحات (Page Routing)
    # ---------------------
    if page == "الرئيسية":
        render_home_page()

    elif page == "تسجيل طالب":
        render_student_page()

    elif page == "تعديل طالب":
        render_edit_student_page()

    elif page == "طلب إجازة":
        render_leave_page()

    elif page == "بريك اليوم":
        render_break_page()

    elif page == "Feedback":
        render_feedback_page()

    elif page == "الشكاوى":
        render_complaints_page()

    elif page == "Dashboard":
        render_dashboard_page()

    elif page == "Report":
        render_report_dashboard()

    elif page == "تسجيل حضور":
        render_attendance_page()

    elif page == "مراجعة البيانات":
        render_data_review_page()
