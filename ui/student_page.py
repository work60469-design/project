# ui/student_page.py

import streamlit as st
from datetime import date

from config.constants import (
    GOVERNORATES,
    STUDENT_STATUS,
    GRADES,
    COURSES,
    NOTES_OPTIONS
)

from services.student_service import (
    save_student
)


def render_student_page():

    st.title("🎓 تسجيل طالب جديد")

    if st.button("✏️ تعديل"):
        st.session_state["go_to_edit_page"] = True
        st.rerun()

    student_name = st.text_input(
        "اسم الطالب"
    )

    student_phone = st.text_input(
        "رقم موبايل الطالب",
        max_chars=11
    )

    governorate = st.selectbox(
        "المحافظة",
        GOVERNORATES
    )

    student_status = st.selectbox(
        "حالة الطالب",
        STUDENT_STATUS
    )

    transfer_phone = st.text_input(
    "الرقم اللى محول منه",
    
    )

    grade = st.selectbox(
        "الصف الدراسي",
        GRADES
    )


    # ---------------------
    # الكورسات حسب الصف
    # ---------------------

    if grade == "أولى ثانوي":

        available_courses = [
            "الترم الاول",
            "شهر 8",
            "شهر 9",
            "شهر 10",
            "شهر 11",
            "شهر 12",
            "شهر 1"
        ]

    else:

        available_courses = [
            "السنوى",
            "الدعامة والحركة",
            "التنسيق الهرمونى",
            "التكاثر",
            "المناعة",
            "DNA & RNA"
        ]


    selected_courses = st.multiselect(
        "اختار الكورسات",
        available_courses
    )


    # أسعار الكورسات

    course_prices = {}

    for course in selected_courses:

        course_prices[course] = st.number_input(
            f"سعر {course}",
            min_value=0,
            step=50,
            key=course
        )


    note = st.selectbox(
        "الملاحظة",
        NOTES_OPTIONS
    )


    note_reason = ""

    if note != "لا يوجد":

        note_reason = st.text_area(
            "سبب الملاحظة"
        )


    registration_date = st.date_input(
        "تاريخ التسجيل",
        value=date.today()
    )


    if st.button("💾 حفظ الطالب"):


        if not student_name.strip():

            st.error("اسم الطالب مطلوب")
            return


        if not student_phone.strip():

            st.error("رقم الموبايل مطلوب")
            return


        if not student_phone.isdigit():

            st.error(
                "رقم الموبايل يجب أن يحتوي أرقام فقط"
            )
            return


        if len(student_phone) != 11:

            st.error(
                "رقم الموبايل يجب أن يكون 11 رقم"
            )
            return


        if not transfer_phone.strip():

            st.error("الرقم اللى محول منه مطلوب")
            return
        

        if not selected_courses:

            st.error(
                "اختار كورس واحد على الأقل"
            )
            return




        # تجهيز البيانات للشيت

        data = {

            "student_name": student_name,
            "student_phone": student_phone,
            "governorate": governorate,
            "student_status": student_status,
            "transfer_phone":transfer_phone,
            "grade": grade,

            "note": note,
            "note_reason": note_reason,

            "registration_date": str(
                registration_date
            ),

            "employee_name":
                st.session_state.display_name

        }


        # إضافة الكورسات وأسعارها

        for course, price in course_prices.items():

            data[course] = price



        save_student(
            **data
        )


        st.success(
            "تم تسجيل الطالب بنجاح ✅"
        )

        st.balloons()