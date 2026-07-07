# services/daily_closure_service.py

import streamlit as st

from datetime import datetime, timedelta

from auth.users import USERS

from services.attendance_service import get_attendance_sheet
from services.feedback_service import get_feedback_sheet


# قد ايه يوم لورا نراجع كل مرة (احتياطي لو حد فوّت فتح
# التطبيق كذا يوم، عشان محدش يفوت من غير ما يتسجل غايب)
DAYS_TO_CHECK_BACK = 1


def _get_employee_names():

    employees = []

    for username, user_data in USERS.items():

        if username == "amal" or username == "sameh":
            continue

        employees.append(
            user_data["display_name"]
        )

    return employees


def _close_out_single_day(
    target_date_str,
    attendance_rows,
    feedback_rows,
    attendance_sheet,
    feedback_sheet,
    employees
):
    """
    يتأكد إن كل موظف عنده صف فى شيت الحضور وصف فى شيت
    الفيدباك ليوم معيّن. لو مفيش، بيضيف صف "غايب" / "لم يتم
    الإرسال" حسب الحالة.
    """

    employees_with_attendance = {
        row.get("اسم الموظف")
        for row in attendance_rows
        if str(row.get("التاريخ", "")).strip() == target_date_str
    }

    employees_with_feedback = {
        row.get("اسم الموظف")
        for row in feedback_rows
        if str(row.get("التاريخ", "")).strip() == target_date_str
    }

    for employee in employees:

        if employee not in employees_with_attendance:

            attendance_sheet.append_row([
                employee,
                target_date_str,
                "",
                "",
                "",
                "غايب"
            ])

        if employee not in employees_with_feedback:

            feedback_sheet.append_row([
                employee,
                "",
                target_date_str,
                "",
                "",
                "",
                "",
                "",
                "",
                "لم يتم الإرسال"
            ])


def close_out_missed_days():
    """
    بتراجع آخر DAYS_TO_CHECK_BACK يوم (من غير النهاردة، لأن
    النهاردة لسه ممكن يحصل فيه حضور أو فيدباك)، ولأي يوم منهم
    فيه موظف معملش حاجة خالص، بتسجله "غايب" فى الحضور و"لم
    يتم الإرسال" فى الفيدباك.

    الفانكشن دي Idempotent: لو اتنادت أكتر من مرة على نفس
    اليوم، مش هتكرر الصفوف، لأنها بتتأكد الأول إن الصف مش
    موجود قبل ما تضيفه.
    """

    employees = _get_employee_names()

    attendance_sheet = get_attendance_sheet()
    feedback_sheet = get_feedback_sheet()

    attendance_rows = attendance_sheet.get_all_records()
    feedback_rows = feedback_sheet.get_all_records()

    today = datetime.now().date()

    for days_back in range(1, DAYS_TO_CHECK_BACK + 1):

        target_date = today - timedelta(days=days_back)

        target_date_str = target_date.strftime("%Y-%m-%d")

        _close_out_single_day(
            target_date_str,
            attendance_rows,
            feedback_rows,
            attendance_sheet,
            feedback_sheet,
            employees
        )


def run_daily_closure_if_needed():
    """
    بتتنادى مرة واحدة (فى app.py مثلاً) كل ما حد يفتح
    التطبيق. بتشغّل الإقفال التلقائي مرة واحدة بس فى اليوم
    لكل جلسة (Session) عشان متعملش قراءة/كتابة زيادة فى
    جوجل شيتس من غير داعي.
    """

    today_str = datetime.now().strftime("%Y-%m-%d")

    if st.session_state.get(
        "daily_closure_checked_for"
    ) == today_str:

        return

    close_out_missed_days()

    st.session_state["daily_closure_checked_for"] = today_str