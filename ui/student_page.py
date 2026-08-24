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

    # ---------------------------------------------------
    # لو فيه رسالة نجاح معلقة من عملية حفظ فاتت (قبل الـ rerun)
    # بنعرضها هنا، عشان تبقى مضمونة الظهور دايمًا مهما كان
    # التوقيت، بدل ما نعتمد على إن st.toast يعدي الـ rerun لوحده
    # ---------------------------------------------------
    if st.session_state.get("pending_toast"):
        st.toast(st.session_state["pending_toast"], icon="✅")
        del st.session_state["pending_toast"]

    if st.button("✏️ تعديل"):
        st.session_state["go_to_edit_page"] = True
        st.rerun()

    # ---------------------------------------------------
    # رقم نسخة الفورم: كل ما نسجل طالب بنزوّد الرقم ده،
    # فكل حقول الإدخال تاخد "مفتاح" جديد وترجع فاضية تلقائيًا
    # (من غير ما نحتاج st.form عشان الكورسات بتتغير حسب الصف)
    # ---------------------------------------------------
    version = st.session_state.get("form_version", 0)

    student_name = st.text_input(
        "اسم الطالب",
        key=f"student_name_{version}"
    )

    student_phone = st.text_input(
        "رقم موبايل الطالب",
        max_chars=11,
        key=f"student_phone_{version}"
    )

    governorate = st.selectbox(
        "المحافظة",
        GOVERNORATES,
        key=f"governorate_{version}"
    )

    student_status = st.selectbox(
        "حالة الطالب",
        STUDENT_STATUS,
        key=f"student_status_{version}"
    )

    transfer_phone = st.text_input(
        "الرقم اللى محول منه",
        key=f"transfer_phone_{version}"
    )

    grade = st.selectbox(
        "الصف الدراسي",
        GRADES,
        key=f"grade_{version}"
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
            "كورس الأحياء والجيولوجيا السنوي",
            "كورس الأحياء السنوي",
            "كورس الجيولوجيا السنوي",
            "الدعامة والحركة",
            "التنسيق الهرمونى",
            "التكاثر",
            "المناعة",
            "DNA & RNA",
            "التراكيب الجيولوجية",
            "المعادن",
            "الصخور"
        ]

    selected_courses = st.multiselect(
        "اختار الكورسات",
        available_courses,
        key=f"courses_{version}"
    )

    # أسعار الكورسات
    course_prices = {}
    for course in selected_courses:
        course_prices[course] = st.number_input(
            f"سعر {course}",
            min_value=0,
            step=50,
            key=f"price_{course}_{version}"
        )

    note = st.selectbox(
        "الملاحظة",
        NOTES_OPTIONS,
        key=f"note_{version}"
    )

    note_reason = ""
    if note != "لا يوجد":
        note_reason = st.text_area(
            "سبب الملاحظة",
            key=f"note_reason_{version}"
        )

    registration_date = st.date_input(
        "تاريخ التسجيل",
        value=date.today(),
        key=f"registration_date_{version}"
    )

    if st.button("💾 حفظ الطالب", key=f"save_btn_{version}"):
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
            "transfer_phone": transfer_phone,
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

        save_student(**data)

        # ---------------------------------------------------
        # 1) نضيف الطالب لقائمة "الطلاب اللي سجلتهم" في الجلسة دي
        #    عشان يبان فورًا قدام الموظف إن التسجيل نجح فعلاً
        # ---------------------------------------------------
        st.session_state.setdefault("my_registered_students", [])
        st.session_state["my_registered_students"].insert(0, data)

        # ---------------------------------------------------
        # 2) رسالة نجاح مؤقتة بتظهر وتختفي لوحدها (توست)
        #    بدل st.success اللي بيفضل ظاهر
        #    بنخزنها فى session_state ونعرضها بعد الـ rerun
        #    (فى أول الدالة) عشان تبقى مضمونة الظهور دايمًا
        # ---------------------------------------------------
        st.session_state["pending_toast"] = "تم تسجيل الطالب بنجاح ✅"

        # ---------------------------------------------------
        # 3) نفضي كل حقول الفورم عن طريق تغيير مفاتيحها
        # ---------------------------------------------------
        st.session_state["form_version"] = version + 1
        st.rerun()

    # ---------------------------------------------------
    # جدول بالطلاب اللي الموظف سجلهم في الجلسة الحالية
    # (تأكيد بصري إن البيانات فعلاً اتسجلت صح)
    # ---------------------------------------------------
    if st.session_state.get("my_registered_students"):
        st.divider()
        st.subheader("✅ آخر الطلاب اللي سجلتهم")
        st.dataframe(
            st.session_state["my_registered_students"],
            use_container_width=True
        )
