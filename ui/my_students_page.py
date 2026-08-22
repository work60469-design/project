# ui/my_students_page.py
import streamlit as st

from services.student_service import get_students_by_employee


def render_my_students_page():
    st.title("📋 الطلاب اللي سجلتهم")

    employee_name = st.session_state.display_name
    students = get_students_by_employee(employee_name)

    if not students:
        st.info("لسه معملتش تسجيل لأي طالب.")
        return

    st.write(
        f"عدد الطلاب اللي سجلتهم: **{len(students)}**"
    )

    search = st.text_input(
        "ابحث بالاسم أو رقم التليفون"
    )

    if search.strip():
        students = [
            s for s in students
            if search.strip() in str(s.get("اسم الطالب", ""))
            or search.strip() in str(s.get("رقم الطالب", ""))
        ]

    st.dataframe(
        students,
        use_container_width=True
    )
