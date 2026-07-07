# ui/home_page.py

import streamlit as st

from datetime import datetime

from services.leave_service import (
    get_leaves_requested_today
)

from services.break_service import (
    get_today_break_changes
)

from services.announcements_service import (
    get_announcements,
    add_announcement,
    delete_announcement
)


def render_announcement_card(announcement):
    """
    كارت واحد لإعلان: بيظهر مصغّر (العنوان + التاريخ + الناشر
    بس)، وبجنبه سهم (expander) لو ضغطت عليه يفتح النص كامل،
    ولو ضغطت تاني يقفل ويرجع صغير زي ما كان.
    زرار المسح بيظهر لامل (الأدمن) بس، جوه الجزء المفتوح.
    """

    title = (
        announcement.get('العنوان', '') or '(بدون عنوان)'
    )

    date_str = announcement.get('تاريخ الإعلان', '')

    author = announcement.get('اسم الناشر', '') or '-'

    expander_label = f"📌 {title}   |   🗓️ {date_str}   |   ✍️ {author}"

    with st.container(border=True):

        with st.expander(expander_label):

            st.write(announcement.get("النص", ""))

            if st.session_state.username == "amal":

                if st.button(
                    "🗑️ مسح الإعلان",
                    key=f"delete_announcement_"
                        f"{announcement.get('_row_number')}"
                ):

                    delete_announcement(
                        announcement["_row_number"]
                    )
                    st.rerun()


def render_announcements_section():
    """
    قسم الإعلانات - بيظهر لكل المستخدمين.
    أي تحديث أو تفصيلة مهمة عايز تنزلها لكل الفريق، بتضيفها
    من هنا (زرار الإضافة بيظهر لامل (الأدمن) بس).
    """

    st.subheader("📢 الإعلانات")

    # رسالة نجاح لو جاي من إضافة إعلان فى الضغطة اللي فاتت
    if st.session_state.get("announcement_just_added"):

        st.success("✅ اتنشر الإعلان بنجاح")
        st.session_state["announcement_just_added"] = False

    if st.session_state.username == "amal":

        with st.expander("➕ إضافة إعلان جديد"):

            with st.form(
                "new_announcement_form",
                clear_on_submit=True
            ):

                announcement_title = st.text_input("العنوان")

                announcement_text = st.text_area(
                    "التفاصيل",
                    height=120,
                    placeholder="اكتب تفاصيل الإعلان أو التحديث الجديد..."
                )

                submitted = st.form_submit_button("📢 نشر الإعلان")

                if submitted:

                    if (
                        not announcement_title.strip()
                        or not announcement_text.strip()
                    ):

                        st.error(
                            "لازم تكتب العنوان والتفاصيل الأول"
                        )

                    else:

                        add_announcement(
                            title=announcement_title,
                            text=announcement_text,
                            employee_name=(
                                st.session_state.display_name
                            )
                        )

                        st.session_state[
                            "announcement_just_added"
                        ] = True

                        st.rerun()

    announcements = get_announcements()

    if not announcements:

        st.info("مفيش إعلانات دلوقتي")

    else:

        latest_announcements = announcements[:3]
        older_announcements = announcements[3:]

        for announcement in latest_announcements:

            render_announcement_card(announcement)

        if older_announcements:

            with st.expander(
                f"📁 أرشيف الإعلانات القديمة "
                f"({len(older_announcements)})"
            ):

                for announcement in older_announcements:

                    render_announcement_card(announcement)

    st.markdown("---")


def render_notifications_section():
    """
    قسم الإشعارات - يظهر لامل (الأدمن) بس، مش لباقي الموظفين.

    دلوقتي فيه إشعارات طلبات الإجازة المقدمة النهاردة.
    لما تتضاف صفحة "الشيفت بريك" بعدين، هتضاف هنا كقسم
    تنبيهات جديد بنفس الطريقة من غير ما نلمس باقي الكود.
    """

    st.subheader("🔔 الإشعارات")

    has_any_notification = False

    # --------------------------
    # إشعارات طلبات الإجازة
    # --------------------------

    today_leave_requests = get_leaves_requested_today()

    if today_leave_requests:

        has_any_notification = True

        for leave in today_leave_requests:

            employee_name = leave.get("اسم الموظف", "")
            leave_type = leave.get("نوع الإجازة", "")
            leave_days = leave.get("عدد الأيام", "")
            start_date = leave.get("تاريخ البداية", "")

            st.warning(
                f"🏖️ **{employee_name}** قدّم طلب إجازة "
                f"**{leave_type}** ({leave_days} يوم) "
                f"يبدأ من {start_date}"
            )

    # --------------------------
    # إشعارات تغيير ميعاد البريك
    # --------------------------

    today_break_changes = get_today_break_changes()

    if today_break_changes:

        has_any_notification = True

        for break_change in today_break_changes:

            employee_name = break_change.get(
                "employee_name", ""
            )

            def _to_arabic_12h(time_str):

                try:

                    parsed = datetime.strptime(
                        time_str, "%H:%M"
                    )

                except (ValueError, TypeError):

                    return time_str

                hour_12 = parsed.hour % 12

                if hour_12 == 0:
                    hour_12 = 12

                period = "م" if parsed.hour >= 12 else "ص"

                return f"{hour_12}:{parsed.minute:02d} {period}"

            start_display = _to_arabic_12h(
                break_change.get("start_time", "")
            )

            end_display = _to_arabic_12h(
                break_change.get("end_time", "")
            )

            st.info(
                f"☕ **{employee_name}** غيّر ميعاد بريكه "
                f"النهاردة لـ {start_display} - {end_display} "
                f"(بدل الميعاد الافتراضي 5-7 مساءً)"
            )

    if not has_any_notification:

        st.success(
            "لا يوجد إشعارات جديدة النهاردة ✅"
        )

    st.markdown("---")


def render_home_page():

    st.title("🎓 Biology Management System")

    st.markdown("---")

    st.subheader(
        f"أهلاً {st.session_state.display_name}"
    )

    # قسم الإعلانات يظهر لكل المستخدمين
    render_announcements_section()

    # قسم الإشعارات يظهر للأدمن (محمد) بس
    if st.session_state.username == "amal":

        render_notifications_section()

    st.info(
        "اختر الصفحة المطلوبة من القائمة الجانبية."
    )