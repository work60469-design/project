# ui/complaints_page.py

import streamlit as st

from services.complaints_service import (
    search_student_by_phone,
    get_complaints_by_phone,
    add_complaint,
    update_complaint
)


GRADE_OPTIONS = ["أولى ثانوي", "3 ثانوي", "غير مسجل"]


def render_complaints_page():

    st.title("📮 الشكاوى")

    # لو جاي من حفظ شكوى فى الضغطة اللي فاتت: امسح كل حاجة
    # وورّي رسالة النجاح دلوقتي (بعد الـ rerun) عشان تتشاف فعلاً
    if st.session_state.get("complaint_just_saved"):

        st.success("✅ اتسجلت الشكوى بنجاح")

        st.session_state["complaint_just_saved"] = False
        st.session_state["complaints_phone_input"] = ""
        st.session_state.pop("complaints_searched_phone", None)

    if st.session_state.get("complaint_edit_saved"):

        st.success("✅ اتعدّلت الشكوى بنجاح")

        st.session_state["complaint_edit_saved"] = False

    st.caption(
        "دوّر برقم موبايل الطالب (أو اللي كلمنا) عشان تجيب "
        "بياناته وتشوف هل فيه شكاوى سابقة عليه، وتقدر تسجّل "
        "شكوى جديدة حتى لو الطالب لسه مااشتركش معانا أصلاً."
    )

    phone_input = st.text_input(
        "📱 رقم الموبايل",
        key="complaints_phone_input",
        placeholder="مثال: 01012345678"
    )

    if st.button("🔍 بحث"):

        if phone_input.strip():
            st.session_state["complaints_searched_phone"] = (
                phone_input.strip()
            )
        else:
            st.warning("اكتب رقم الموبايل الأول")

    searched_phone = st.session_state.get("complaints_searched_phone")

    if not searched_phone:
        st.info("دوّر برقم الموبايل الأول عشان تكمّل")
        return

    st.divider()

    # ==================================
    # 👤 بيانات الطالب
    # ==================================

    st.subheader("👤 بيانات الطالب")

    student_records = search_student_by_phone(searched_phone)

    if student_records:

        for record in student_records:

            with st.container(border=True):

                st.markdown(
                    f"**{record['اسم الطالب'] or '(بدون اسم)'}** "
                    f"— {record['الصف']}"
                )

                st.write(
                    f"📱 {record['رقم الطالب']}  |  "
                    f"🗺️ {record['المحافظة'] or '-'}  |  "
                    f"🏷️ الحالة: {record['الحالة'] or '-'}  |  "
                    f"📝 الملاحظة: {record['الملاحظة'] or '-'}"
                )

                if str(record["سبب الملاحظة"]).strip():
                    st.caption(
                        f"سبب الملاحظة: {record['سبب الملاحظة']}"
                    )

                st.caption(
                    f"📚 الكورسات: {record['الكورسات المشترك فيها']}  |  "
                    f"📅 تاريخ التسجيل: {record['تاريخ التسجيل'] or '-'}  |  "
                    f"👤 الموظف المسؤول: {record['اسم الموظف'] or '-'}"
                )

    else:

        st.warning(
            "الرقم ده مش مسجّل فى بيانات الطلاب — يبقى غالبًا "
            "حد كلّمكم بس لسه مااشتركش، وممكن تسجّل شكوى بيه "
            "بالاسم ورقم الموبايل بس من غير مشكلة."
        )

    st.divider()

    # ==================================
    # 📜 الشكاوى السابقة لنفس الرقم
    # ==================================

    st.subheader("📜 الشكاوى السابقة لنفس الرقم")

    previous_complaints = get_complaints_by_phone(searched_phone)

    if previous_complaints:

        st.error(
            f"⚠️ فيه {len(previous_complaints)} شكوى سابقة "
            f"مسجّلة على الرقم ده — راجعها قبل ما تتصرف"
        )

        for complaint in previous_complaints:

            with st.container(border=True):

                st.markdown(
                    f"📅 **{complaint.get('تاريخ الشكوى', '')}**  |  "
                    f"👤 {complaint.get('اسم الموظف', '') or '-'}"
                )

                st.write(
                    complaint.get("نص الشكوى", "") or "-"
                )

                if str(
                    complaint.get("تم الحظر", "")
                ).strip() == "نعم":

                    st.caption("🚫 اتحظر الطالب بعد الشكوى دي")

                row_number = complaint.get("_row_number")

                with st.expander("✏️ تعديل الشكوى دي"):

                    edit_key = f"edit_complaint_{row_number}"

                    current_grade = complaint.get("الصف", "غير مسجل")

                    edited_name = st.text_input(
                        "اسم الطالب",
                        value=complaint.get("اسم الطالب", ""),
                        key=f"{edit_key}_name"
                    )

                    edited_grade = st.selectbox(
                        "الصف",
                        GRADE_OPTIONS,
                        index=(
                            GRADE_OPTIONS.index(current_grade)
                            if current_grade in GRADE_OPTIONS
                            else 2
                        ),
                        key=f"{edit_key}_grade"
                    )

                    edited_text = st.text_area(
                        "نص الشكوى",
                        value=complaint.get("نص الشكوى", ""),
                        height=100,
                        key=f"{edit_key}_text"
                    )

                    edited_banned = st.checkbox(
                        "🚫 تم حظر الطالب / منعه من الاشتراك تاني",
                        value=(
                            str(
                                complaint.get("تم الحظر", "")
                            ).strip() == "نعم"
                        ),
                        key=f"{edit_key}_banned"
                    )

                    if st.button(
                        "💾 حفظ التعديل",
                        key=f"{edit_key}_save"
                    ):

                        if not edited_text.strip():

                            st.error("لازم تكتب نص الشكوى")

                        else:

                            update_complaint(
                                row_number=row_number,
                                student_name=edited_name,
                                grade_label=edited_grade,
                                complaint_text=edited_text,
                                banned=edited_banned
                            )

                            st.session_state[
                                "complaint_edit_saved"
                            ] = True

                            st.rerun()

    else:

        st.success("✅ مفيش شكاوى سابقة مسجّلة على الرقم ده")

    st.divider()

    # ==================================
    # ➕ تسجيل شكوى جديدة
    # ==================================

    st.subheader("➕ تسجيل شكوى جديدة")

    default_name = (
        student_records[0]["اسم الطالب"] if student_records else ""
    )

    default_grade = (
        student_records[0]["الصف"]
        if student_records else "غير مسجل"
    )

    default_grade_index = (
        GRADE_OPTIONS.index(default_grade)
        if default_grade in GRADE_OPTIONS else 2
    )

    with st.form("new_complaint_form", clear_on_submit=True):

        complaint_name = st.text_input(
            "اسم الطالب",
            value=default_name
        )

        complaint_grade = st.selectbox(
            "الصف",
            GRADE_OPTIONS,
            index=default_grade_index
        )

        complaint_text = st.text_area(
            "نص الشكوى",
            height=120,
            placeholder="اكتب المشكلة اللي حصلت بالتفصيل..."
        )

        complaint_banned = st.checkbox(
            "🚫 تم حظر الطالب / منعه من الاشتراك تاني"
        )

        submitted = st.form_submit_button("💾 حفظ الشكوى")

        if submitted:

            if not complaint_text.strip():

                st.error("لازم تكتب نص الشكوى الأول")

            else:

                current_employee_name = st.session_state.get(
                    "display_name", ""
                )

                add_complaint(
                    phone=searched_phone,
                    student_name=complaint_name,
                    grade_label=complaint_grade,
                    complaint_text=complaint_text,
                    employee_name=current_employee_name,
                    banned=complaint_banned
                )

                st.session_state["complaint_just_saved"] = True
                st.rerun()