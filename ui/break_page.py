# ui/break_page.py

import streamlit as st

from datetime import datetime, time, timedelta

from services.break_service import (
    get_today_break,
    save_break,
    update_break,
    DEFAULT_BREAK_START_HOUR,
    DEFAULT_BREAK_DURATION_HOURS,
    STATUS_DEFAULT
)


def format_time_12h(time_obj):
    """
    بتحول وقت (time object) لصيغة 12 ساعة بالعربي، زي: "5:00 م"
    """

    hour_24 = time_obj.hour

    period = "م" if hour_24 >= 12 else "ص"

    hour_12 = hour_24 % 12

    if hour_12 == 0:
        hour_12 = 12

    return f"{hour_12}:{time_obj.minute:02d} {period}"


def render_12h_time_picker(default_time, key_prefix):
    """
    بديل لـ st.time_input بنظام 12 ساعة (ص/م) بدل 24 ساعة،
    عشان يكون أسهل فى الاستخدام.
    """

    default_hour_24 = default_time.hour

    default_period = "م" if default_hour_24 >= 12 else "ص"

    default_hour_12 = default_hour_24 % 12

    if default_hour_12 == 0:
        default_hour_12 = 12

    minute_options = [0, 15, 30, 45]

    default_minute_index = 0

    if default_time.minute in minute_options:
        default_minute_index = minute_options.index(
            default_time.minute
        )

    col1, col2, col3 = st.columns(3)

    with col1:

        hour_12 = st.selectbox(
            "الساعة",
            list(range(1, 13)),
            index=default_hour_12 - 1,
            key=f"{key_prefix}_hour"
        )

    with col2:

        minute = st.selectbox(
            "الدقيقة",
            minute_options,
            index=default_minute_index,
            format_func=lambda m: f"{m:02d}",
            key=f"{key_prefix}_minute"
        )

    with col3:

        period = st.selectbox(
            "ص / م",
            ["ص", "م"],
            index=0 if default_period == "ص" else 1,
            key=f"{key_prefix}_period"
        )

    hour_24 = hour_12 % 12

    if period == "م":
        hour_24 += 12

    return time(hour_24, minute)


def render_break_page():

    st.title("☕ بريك اليوم")

    employee_name = st.session_state.display_name

    today_str = datetime.now().strftime(
        "%Y-%m-%d"
    )

    default_start = time(
        DEFAULT_BREAK_START_HOUR,
        0
    )

    existing = get_today_break(
        employee_name
    )

    if existing:

        old_data = existing["data"]

        try:

            old_start_display = format_time_12h(
                datetime.strptime(
                    old_data["start_time"], "%H:%M"
                ).time()
            )

            old_end_display = format_time_12h(
                datetime.strptime(
                    old_data["end_time"], "%H:%M"
                ).time()
            )

        except (ValueError, TypeError):

            old_start_display = old_data["start_time"]
            old_end_display = old_data["end_time"]

        st.info(
            f"✅ بريك النهاردة محفوظ: من "
            f"{old_start_display} لحد "
            f"{old_end_display} "
            f"({old_data['status']})"
        )

        st.markdown(
            "**عاوز تغيّره؟ عدّل الميعاد تحت واحفظ تاني.**"
        )

        try:

            current_start = datetime.strptime(
                old_data["start_time"],
                "%H:%M"
            ).time()

        except (ValueError, TypeError):

            current_start = default_start

    else:

        old_data = None
        current_start = default_start

        st.info(
            f"⏰ الميعاد الافتراضي للبريك: من "
            f"{format_time_12h(default_start)} "
            f"لمدة {DEFAULT_BREAK_DURATION_HOURS} ساعة "
            f"(يعني لحد {format_time_12h(time(19, 0))})"
        )

    st.markdown("---")

    is_currently_default = (
        old_data is None
        or
        old_data["status"] == STATUS_DEFAULT
    )

    use_default = st.checkbox(
        "هستخدم الميعاد الافتراضي (5 - 7 مساءً)",
        value=is_currently_default,
        key="use_default_break"
    )

    if use_default:

        start_time_value = default_start

    else:

        st.write(
            "اختار ميعاد بداية البريك بتاعك النهاردة "
            f"(هيكون لمدة {DEFAULT_BREAK_DURATION_HOURS} ساعة):"
        )

        start_time_value = render_12h_time_picker(
            current_start,
            "custom_break_start"
        )

    end_datetime = (
        datetime.combine(
            datetime.today(),
            start_time_value
        )
        +
        timedelta(hours=DEFAULT_BREAK_DURATION_HOURS)
    )

    end_time_value = end_datetime.time()

    st.info(
        f"📌 البريك هيكون من "
        f"{format_time_12h(start_time_value)} "
        f"لحد {format_time_12h(end_time_value)}"
    )

    button_label = (
        "💾 حفظ التعديل" if existing else "✅ تأكيد البريك"
    )

    if st.button(button_label):

        start_str = start_time_value.strftime("%H:%M")
        end_str = end_time_value.strftime("%H:%M")

        if existing:

            update_break(
                row_number=existing["row_number"],
                employee_name=employee_name,
                break_date=today_str,
                start_time=start_str,
                end_time=end_str
            )

        else:

            save_break(
                employee_name=employee_name,
                break_date=today_str,
                start_time=start_str,
                end_time=end_str
            )

        st.success(
            "تم حفظ بريك النهاردة بنجاح ✅"
        )

        st.rerun()