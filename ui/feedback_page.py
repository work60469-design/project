# ui/feedback_page.py

import streamlit as st

from datetime import datetime

from services.feedback_service import (
    save_feedback,
    update_feedback,
    get_today_feedback,
    get_last_feedback,
    is_feedback_editable,
    EDIT_GRACE_HOUR
)


SUPPORT_TASKS = [
    "الرد على استفسارات الطلاب",
    "حل مشاكل تسجيل الدخول",
    "تفعيل الاشتراكات على المنصه",
    "تسجيل الاشتراكات فى الشيت",
    "تنزيل استوريهات",
    "الاطمئنان على الطلاب وتحفيزهم",
    "تجميع فيدباك الطلاب",
    "ترويج للمستر على الجروبات وترشيحه"
]

SOCIAL_TASKS = [
    "الرد على تعليقات ورسائل فيسبوك/يوتيوب/انستجرام",
    "الرد على استفسارات المهتمين على الخاص",
    "الاستماع الى الجزء الاول والاخير من المحاضره"
]

FOLLOWUP_TASKS = [
    "استخراج بيانات الطلاب",
    "تنزيل الشيت وتقسيمه",
    "الترحيب بالطلاب الجدد",
    "التواصل مع الطلاب بخصوص المحاضرات",
    "التواصل مع الطلاب بخصوص الامتحان",
    "التواصل مع أولياء الأمور بخصوص المستوى أو الغياب",
    "الرد على استفسارات الطلاب",
    "تنزيل استوريهات",
    "دعم نفسى",
    "مراجعة الشيت والتحقق من صحة البيانات",
    "متابعة التخفيض والمجانى"
]


def to_int_safe(value, default=0):

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def render_star_rating(default_value, key):
    """
    تقييم بالنجوم بدل السلايدر (1-5)، بديل بسيط ومتوافق مع أي
    نسخة Streamlit عن طريق radio أفقي بشكل نجوم.
    """

    if default_value not in [1, 2, 3, 4, 5]:
        default_value = 5

    selected = st.radio(
        "⭐ التقييم",
        options=[1, 2, 3, 4, 5],
        index=default_value - 1,
        format_func=lambda n: "⭐" * n,
        horizontal=True,
        key=key
    )

    return selected


def parse_existing_report(report_text, tasks_list):
    """
    بتاخد نص تقرير محفوظ قبل كده وتفصل المهام الثابتة
    (اللي موجودة فى tasks_list) عن أي سطور إضافية حرة.
    """

    if not report_text:
        return [], ""

    lines = [
        line.strip()
        for line in report_text.split("\n")
        if line.strip()
    ]

    matched = [
        line for line in lines
        if line in tasks_list
    ]

    leftover = [
        line for line in lines
        if line not in tasks_list
    ]

    return matched, "\n".join(leftover)


def render_tasks_section(
    tasks_list,
    department_key,
    mode_suffix,
    default_selected=None,
    default_extra=""
):
    """
    بتعرض تشيك بوكس لكل مهمة ثابتة + خانة لمهام إضافية،
    وترجع نص التقرير النهائي جاهز للحفظ.
    """

    if default_selected is None:
        default_selected = []

    st.write(
        "✅ اختار المهام اللي عملتها النهاردة:"
    )

    selected_tasks = []

    for task in tasks_list:

        checked = st.checkbox(
            task,
            value=(task in default_selected),
            key=f"task_{department_key}_{task}_{mode_suffix}"
        )

        if checked:
            selected_tasks.append(task)

    extra_tasks = st.text_area(
        "➕ مهام إضافية (لو عملت حاجة مش موجودة فى الاختيارات فوق)",
        value=default_extra,
        key=f"extra_{department_key}_{mode_suffix}"
    )

    report_parts = selected_tasks.copy()

    if extra_tasks.strip():

        report_parts.append(
            extra_tasks.strip()
        )

    report = "\n".join(report_parts)

    return report


def render_feedback_page():

    st.title(
        "📝 Feedback"
    )

    employee_name = (
        st.session_state.display_name
    )

    role = (
        st.session_state.role
    )

    today_str = datetime.now().strftime(
        "%Y-%m-%d"
    )

    existing_today = get_today_feedback(
        employee_name
    )

    if "feedback_edit_mode" not in st.session_state:
        st.session_state["feedback_edit_mode"] = False

    # ==================================
    # الحالة أ: بعت فيدباك النهاردة بالفعل
    # ==================================

    if existing_today:

        st.success(
            "✅ تم إرسال Feedback اليوم بالفعل"
        )

        if st.button("✏️ تعديل"):
            st.session_state["feedback_edit_mode"] = True

        if not st.session_state["feedback_edit_mode"]:
            return

        old_data = existing_today["data"]
        edit_row_number = existing_today["row_number"]
        mode_suffix = f"edit_{edit_row_number}"
        is_edit_mode = True

        st.markdown("---")
        st.write("**تعديل آخر Feedback بعتته النهاردة:**")

    # ==================================
    # الحالة ب: لسه مبعتش النهاردة
    # (تحقق لو فيه فيدباك شيفت فات لسه فى فترة السماح)
    # ==================================

    else:

        last_feedback = get_last_feedback(
            employee_name
        )

        grace_available = (
            last_feedback is not None
            and
            is_feedback_editable(
                last_feedback["data"]["feedback_date"]
            )
        )

        if grace_available:

            st.info(
                f"📌 لسه ممكن تعدل فيدباك يوم "
                f"{last_feedback['data']['feedback_date']} "
                f"لحد الساعة {EDIT_GRACE_HOUR} صباحًا."
            )

            col1, col2 = st.columns(2)

            with col1:

                if st.button(
                    "✏️ تعديل فيدباك الشيفت اللي فات"
                ):
                    st.session_state["feedback_edit_mode"] = True

            with col2:

                if st.button(
                    "📝 تسجيل فيدباك جديد للنهاردة"
                ):
                    st.session_state["feedback_edit_mode"] = False

            st.markdown("---")

        if grace_available and st.session_state["feedback_edit_mode"]:

            old_data = last_feedback["data"]
            edit_row_number = last_feedback["row_number"]
            mode_suffix = f"edit_{edit_row_number}"
            is_edit_mode = True

            st.write(
                f"**تعديل Feedback بتاريخ "
                f"{old_data['feedback_date']}:**"
            )

        else:

            old_data = {}
            edit_row_number = None
            mode_suffix = "new"
            is_edit_mode = False

    # ==================================
    # Support Team
    # ==================================

    if role == "support":

        st.subheader(
            "📞 Feedback الدعم الفني"
        )

        activations = st.number_input(
            "عدد التفعيلات",
            min_value=0,
            step=1,
            value=to_int_safe(
                old_data.get("activations", 0)
            )
        )

        rating = render_star_rating(
            to_int_safe(old_data.get("rating", 5), default=5),
            key=f"rating_support_{mode_suffix}"
        )

        matched_tasks, leftover_text = parse_existing_report(
            old_data.get("report", ""),
            SUPPORT_TASKS
        )

        report = render_tasks_section(
            SUPPORT_TASKS,
            "support",
            mode_suffix,
            default_selected=matched_tasks,
            default_extra=leftover_text
        )

        button_label = (
            "💾 حفظ التعديل" if is_edit_mode else "إرسال"
        )

        if st.button(button_label):

            if report.strip() == "":

                st.error(
                    "يجب اختيار مهمة واحدة على الأقل "
                    "أو كتابة مهمة إضافية"
                )

            else:

                if is_edit_mode:

                    update_feedback(
                        row_number=edit_row_number,
                        employee_name=employee_name,
                        department="Support",
                        feedback_date=old_data.get(
                            "feedback_date", today_str
                        ),
                        activations=activations,
                        calls_count="",
                        answered_count="",
                        rating=rating,
                        report=report,
                        submission_time=old_data.get(
                            "submission_time", ""
                        ),
                        lateness_status=old_data.get(
                            "lateness_status", ""
                        )
                    )

                else:

                    save_feedback(
                        employee_name,
                        "Support",
                        today_str,
                        activations,
                        "",
                        "",
                        rating,
                        report
                    )

                st.success(
                    "تم الحفظ بنجاح ✅"
                )

                st.session_state["feedback_edit_mode"] = False

                st.rerun()

    # ==================================
    # Social Team
    # ==================================

    elif role == "social":

        st.subheader(
            "📱 Feedback السوشيال ميديا"
        )

        rating = render_star_rating(
            to_int_safe(old_data.get("rating", 5), default=5),
            key=f"rating_social_{mode_suffix}"
        )

        matched_tasks, leftover_text = parse_existing_report(
            old_data.get("report", ""),
            SOCIAL_TASKS
        )

        report = render_tasks_section(
            SOCIAL_TASKS,
            "social",
            mode_suffix,
            default_selected=matched_tasks,
            default_extra=leftover_text
        )

        button_label = (
            "💾 حفظ التعديل" if is_edit_mode else "إرسال"
        )

        if st.button(button_label):

            if report.strip() == "":

                st.error(
                    "يجب اختيار مهمة واحدة على الأقل "
                    "أو كتابة مهمة إضافية"
                )

            else:

                if is_edit_mode:

                    update_feedback(
                        row_number=edit_row_number,
                        employee_name=employee_name,
                        department="Social",
                        feedback_date=old_data.get(
                            "feedback_date", today_str
                        ),
                        activations="",
                        calls_count="",
                        answered_count="",
                        rating=rating,
                        report=report,
                        submission_time=old_data.get(
                            "submission_time", ""
                        ),
                        lateness_status=old_data.get(
                            "lateness_status", ""
                        )
                    )

                else:

                    save_feedback(
                        employee_name,
                        "Social",
                        today_str,
                        "",
                        "",
                        "",
                        rating,
                        report
                    )

                st.success(
                    "تم الحفظ بنجاح ✅"
                )

                st.session_state["feedback_edit_mode"] = False

                st.rerun()

    # ==================================
    # Followup Team
    # ==================================

    elif role == "followup":

        st.subheader(
            "☎️ Feedback المتابعة"
        )

        calls_count = st.number_input(
            "عدد المكالمات",
            min_value=0,
            step=1,
            value=to_int_safe(
                old_data.get("calls_count", 0)
            )
        )

        answered_count = st.number_input(
            "عدد الطلاب الذين ردوا",
            min_value=0,
            step=1,
            value=to_int_safe(
                old_data.get("answered_count", 0)
            )
        )

        rating = render_star_rating(
            to_int_safe(old_data.get("rating", 5), default=5),
            key=f"rating_followup_{mode_suffix}"
        )

        matched_tasks, leftover_text = parse_existing_report(
            old_data.get("report", ""),
            FOLLOWUP_TASKS
        )

        report = render_tasks_section(
            FOLLOWUP_TASKS,
            "followup",
            mode_suffix,
            default_selected=matched_tasks,
            default_extra=leftover_text
        )

        button_label = (
            "💾 حفظ التعديل" if is_edit_mode else "إرسال"
        )

        if st.button(button_label):

            if answered_count > calls_count:

                st.error(
                    "عدد الردود لا يمكن أن يكون أكبر من عدد المكالمات"
                )

            elif report.strip() == "":

                st.error(
                    "يجب اختيار مهمة واحدة على الأقل "
                    "أو كتابة مهمة إضافية"
                )

            else:

                if is_edit_mode:

                    update_feedback(
                        row_number=edit_row_number,
                        employee_name=employee_name,
                        department="Followup",
                        feedback_date=old_data.get(
                            "feedback_date", today_str
                        ),
                        activations="",
                        calls_count=calls_count,
                        answered_count=answered_count,
                        rating=rating,
                        report=report,
                        submission_time=old_data.get(
                            "submission_time", ""
                        ),
                        lateness_status=old_data.get(
                            "lateness_status", ""
                        )
                    )

                else:

                    save_feedback(
                        employee_name,
                        "Followup",
                        today_str,
                        "",
                        calls_count,
                        answered_count,
                        rating,
                        report
                    )

                st.success(
                    "تم الحفظ بنجاح ✅"
                )

                st.session_state["feedback_edit_mode"] = False

                st.rerun()