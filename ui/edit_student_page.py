# ui/edit_student_page.py

import streamlit as st
from datetime import date, datetime

from config.constants import (
    GOVERNORATES,
    STUDENT_STATUS,
    NOTES_OPTIONS
)

from services.student_service import (
    find_students_by_phone,
    update_student,
    delete_student,
    normalize_phone,
    log_edit
)


COURSES_GRADE_1 = [
    "الترم الاول",
    "شهر 8",
    "شهر 9",
    "شهر 10",
    "شهر 11",
    "شهر 12",
    "شهر 1"
]

COURSES_OTHER_GRADES = [
    "السنوى",
    "الدعامة والحركة",
    "التنسيق الهرمونى",
    "التكاثر",
    "المناعة",
    "DNA & RNA"
]


def get_courses_for_grade(grade):

    if grade == "أولى ثانوي":
        return COURSES_GRADE_1

    return COURSES_OTHER_GRADES


def build_changes_summary(
    old_data,
    available_courses,
    new_student_name,
    new_student_phone,
    new_governorate,
    new_student_status,
    new_transfer_phone,
    new_note,
    new_note_reason,
    new_registration_date,
    new_course_prices,
    new_selected_courses
):
    """
    يقارن بين البيانات القديمة والجديدة ويرجع نص واضح
    يوصف بس الحقول اللي اتغيرت فعلا.
    """

    changes = []

    simple_fields = [
        (
            "اسم الطالب",
            old_data.get("اسم الطالب", ""),
            new_student_name
        ),
        (
            "رقم موبايل الطالب",
            normalize_phone(old_data.get("رقم الطالب", "")),
            new_student_phone
        ),
        (
            "المحافظة",
            old_data.get("المحافظة", ""),
            new_governorate
        ),
        (
            "حالة الطالب",
            old_data.get("الحالة", ""),
            new_student_status
        ),
        (
            "الرقم اللى محول منه",
            normalize_phone(old_data.get("الرقم اللى محول منه", "")),
            new_transfer_phone
        ),
        (
            "الملاحظة",
            old_data.get("الملاحظة", ""),
            new_note
        ),
        (
            "سبب الملاحظة",
            old_data.get("سبب الملاحظة", ""),
            new_note_reason
        ),
        (
            "تاريخ التسجيل",
            str(old_data.get("تاريخ التسجيل", "")),
            new_registration_date
        ),
    ]

    for label, old_value, new_value in simple_fields:

        old_str = str(old_value).strip()
        new_str = str(new_value).strip()

        if old_str != new_str:
            changes.append(
                f"{label}: من '{old_str}' لـ '{new_str}'"
            )


    for course in available_courses:

        old_str = str(old_data.get(course, "")).strip()

        if course in new_selected_courses:
            new_str = str(new_course_prices.get(course, "")).strip()
        else:
            new_str = ""

        if old_str != new_str:

            if old_str == "" and new_str != "":
                changes.append(
                    f"{course}: تم إضافته بسعر {new_str}"
                )

            elif old_str != "" and new_str == "":
                changes.append(
                    f"{course}: تم حذفه (كان بسعر {old_str})"
                )

            else:
                changes.append(
                    f"{course}: السعر من {old_str} لـ {new_str}"
                )


    if not changes:
        return "لم يحدث أي تغيير فعلي"

    return " | ".join(changes)


def render_edit_student_page():

    st.title("✏️ تعديل بيانات طالب")

    search_phone = st.text_input(
        "دخل رقم موبايل الطالب للبحث",
        key="edit_search_phone"
    )

    if st.button("🔍 بحث"):

        if not search_phone.strip():

            st.error("دخل رقم الموبايل للبحث")

        else:

            results = find_students_by_phone(search_phone)
            st.session_state["edit_search_results"] = results

            if not results:
                st.warning("لا يوجد أي تسجيل بهذا الرقم")


    results = st.session_state.get("edit_search_results", [])

    if not results:
        return


    # ---------------------
    # اختيار التسجيل المطلوب تعديله
    # ---------------------

    options_labels = []

    for r in results:

        d = r["data"]

        label = (
            f"{d.get('اسم الطالب', '')} | "
            f"الصف: {d.get('الصف', '')} | "
            f"تاريخ التسجيل: {d.get('تاريخ التسجيل', '')} | "
            f"سجله: {d.get('اسم الموظف', '')}"
        )

        options_labels.append(label)

    selected_index = st.radio(
        "اختار التسجيل اللي عاوز تعدله",
        options=range(len(options_labels)),
        format_func=lambda i: options_labels[i],
        key="edit_selected_index"
    )

    selected_record = results[selected_index]
    data = selected_record["data"]
    grade = data.get("الصف", "")

    # معرف فريد للتسجيل ده، بنستخدمه فى الـ key بتاع كل حقل
    # عشان لما تختار طالب/تسجيل تاني، الحقول تتفرغ صح
    # من بيانات التسجيل الجديد ومتفضلش شايفة القيم القديمة
    record_id = f"{selected_record['sheet_name']}_{selected_record['row_number']}"


    st.markdown("---")
    st.subheader(f"تعديل بيانات: {data.get('اسم الطالب', '')}")


    student_name = st.text_input(
        "اسم الطالب",
        value=data.get("اسم الطالب", ""),
        key=f"edit_student_name_{record_id}"
    )

    student_phone = st.text_input(
        "رقم موبايل الطالب",
        value=normalize_phone(data.get("رقم الطالب", "")),
        max_chars=11,
        key=f"edit_student_phone_{record_id}"
    )

    governorate_default = data.get("المحافظة", "")
    governorate = st.selectbox(
        "المحافظة",
        GOVERNORATES,
        index=(
            GOVERNORATES.index(governorate_default)
            if governorate_default in GOVERNORATES else 0
        ),
        key=f"edit_governorate_{record_id}"
    )

    status_default = data.get("الحالة", "")
    student_status = st.selectbox(
        "حالة الطالب",
        STUDENT_STATUS,
        index=(
            STUDENT_STATUS.index(status_default)
            if status_default in STUDENT_STATUS else 0
        ),
        key=f"edit_student_status_{record_id}"
    )

    transfer_phone = st.text_input(
        "الرقم اللى محول منه",
        value=normalize_phone(data.get("الرقم اللى محول منه", "")),
        key=f"edit_transfer_phone_{record_id}"
    )

    st.text_input(
        "الصف الدراسي (غير قابل للتعديل)",
        value=grade,
        disabled=True
    )


    # ---------------------
    # الكورسات
    # ---------------------

    available_courses = get_courses_for_grade(grade)

    existing_selected_courses = [
        c for c in available_courses
        if str(data.get(c, "")).strip() != ""
    ]

    selected_courses = st.multiselect(
        "اختار الكورسات",
        available_courses,
        default=existing_selected_courses,
        key=f"edit_selected_courses_{record_id}"
    )

    course_prices = {}

    for course in selected_courses:

        existing_value = data.get(course, 0)

        try:
            existing_value = int(existing_value)
        except (ValueError, TypeError):
            existing_value = 0

        course_prices[course] = st.number_input(
            f"سعر {course}",
            min_value=0,
            step=50,
            value=existing_value,
            key=f"edit_price_{course}_{record_id}"
        )


    note_default = data.get("الملاحظة", "")
    note = st.selectbox(
        "الملاحظة",
        NOTES_OPTIONS,
        index=(
            NOTES_OPTIONS.index(note_default)
            if note_default in NOTES_OPTIONS else 0
        ),
        key=f"edit_note_{record_id}"
    )

    note_reason = ""

    if note != "لا يوجد":

        note_reason = st.text_area(
            "سبب الملاحظة",
            value=data.get("سبب الملاحظة", ""),
            key=f"edit_note_reason_{record_id}"
        )


    registration_date_default = data.get("تاريخ التسجيل", "")

    try:
        registration_date_value = datetime.strptime(
            registration_date_default, "%Y-%m-%d"
        ).date()
    except (ValueError, TypeError):
        registration_date_value = date.today()

    registration_date = st.date_input(
        "تاريخ التسجيل",
        value=registration_date_value,
        key=f"edit_registration_date_{record_id}"
    )


    if st.button("💾 حفظ التعديلات"):

        if not student_name.strip():
            st.error("اسم الطالب مطلوب")
            return

        if not student_phone.strip():
            st.error("رقم الموبايل مطلوب")
            return

        if not student_phone.isdigit():
            st.error("رقم الموبايل يجب أن يحتوي أرقام فقط")
            return

        if len(student_phone) != 11:
            st.error("رقم الموبايل يجب أن يكون 11 رقم")
            return

        if not transfer_phone.strip():
            st.error("الرقم اللى محول منه مطلوب")
            return

        if not selected_courses:
            st.error("اختار كورس واحد على الأقل")
            return

        changes_text = build_changes_summary(
            old_data=data,
            available_courses=available_courses,
            new_student_name=student_name,
            new_student_phone=student_phone,
            new_governorate=governorate,
            new_student_status=student_status,
            new_transfer_phone=transfer_phone,
            new_note=note,
            new_note_reason=note_reason,
            new_registration_date=str(registration_date),
            new_course_prices=course_prices,
            new_selected_courses=selected_courses
        )

        update_student(
            sheet_name=selected_record["sheet_name"],
            row_number=selected_record["row_number"],
            student_name=student_name,
            student_phone=student_phone,
            governorate=governorate,
            student_status=student_status,
            transfer_phone=transfer_phone,
            grade=grade,
            note=note,
            note_reason=note_reason,
            registration_date=str(registration_date),
            employee_name=st.session_state.display_name,
            **course_prices
        )

        log_edit(
            employee_name=st.session_state.display_name,
            student_name=student_name,
            student_phone=student_phone,
            grade=grade,
            sheet_name=selected_record["sheet_name"],
            row_number=selected_record["row_number"],
            changes_text=changes_text
        )

        st.success("تم تعديل بيانات الطالب بنجاح ✅")

        # تحديث النتيجة المعروضة عشان تفضل متزامنة لو عدل تاني مرة
        st.session_state["edit_search_results"] = find_students_by_phone(
            student_phone
        )


    # ---------------------
    # منطقة الحذف
    # ---------------------

    st.markdown("---")

    with st.expander("🗑️ حذف هذا التسجيل نهائيًا"):

        st.warning(
            "الإجراء ده نهائي ومش هينفع ترجع فيه بعد كده. "
            "تأكد إنك واخد التسجيل الصحيح قبل الحذف."
        )

        confirm_delete = st.checkbox(
            "أنا متأكد إني عاوز أحذف هذا التسجيل بالكامل",
            key=f"confirm_delete_{record_id}"
        )

        if st.button(
            "🗑️ حذف التسجيل نهائيًا",
            key=f"delete_button_{record_id}"
        ):

            if not confirm_delete:

                st.error(
                    "لازم تعمل تيك على تأكيد الحذف أولاً"
                )

            else:

                delete_student(
                    sheet_name=selected_record["sheet_name"],
                    row_number=selected_record["row_number"]
                )

                log_edit(
                    employee_name=st.session_state.display_name,
                    student_name=data.get("اسم الطالب", ""),
                    student_phone=normalize_phone(
                        data.get("رقم الطالب", "")
                    ),
                    grade=grade,
                    sheet_name=selected_record["sheet_name"],
                    row_number=selected_record["row_number"],
                    changes_text="تم حذف هذا التسجيل بالكامل"
                )

                st.success("تم حذف التسجيل بنجاح ✅")

                # تحديث نتائج البحث وتفريغ الاختيار القديم
                st.session_state["edit_search_results"] = (
                    find_students_by_phone(search_phone)
                )

                if "edit_selected_index" in st.session_state:
                    del st.session_state["edit_selected_index"]

                st.rerun()