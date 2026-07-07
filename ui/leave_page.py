# ui/leave_page.py

import streamlit as st
import pandas as pd

from datetime import date
from datetime import timedelta

from services.leave_service import (
    calculate_return_date,
    save_leave,
    get_leave_statistics,
    get_available_planned_days,
    get_employee_leaves
)


def render_leave_page():

    st.title("🏖️ طلب إجازة")

    # ==================================
    # Statistics
    # ==================================

    stats = get_leave_statistics(
        st.session_state.display_name
    )

    st.subheader(
        "📊 رصيد الإجازات"
    )

    st.write(
        f"الطارئة: {stats['emergency_used']} / 6"
    )

    st.progress(
        min(
            stats["emergency_used"] / 6,
            1.0
        )
    )

    st.write(
        f"المتبقي: {stats['emergency_remaining']}"
    )

    st.divider()

    st.write(
        f"المخططة (شهري): "
        f"{stats['planned_monthly_used']} / 5"
    )

    st.progress(
        min(
            stats["planned_monthly_used"] / 5,
            1.0
        )
    )

    st.write(
        f"المتبقي: "
        f"{stats['planned_monthly_remaining']}"
    )

    st.divider()

    st.write(
        f"المخططة (سنوي): "
        f"{stats['planned_yearly_used']} / 15"
    )

    st.progress(
        min(
            stats["planned_yearly_used"] / 15,
            1.0
        )
    )

    st.write(
        f"المتبقي: "
        f"{stats['planned_yearly_remaining']}"
    )

    st.divider()

    # ==================================
    # سجل الإجازات السابقة
    # ==================================

    st.subheader(
        "📋 سجل إجازاتك"
    )

    my_leaves = get_employee_leaves(
        st.session_state.display_name
    )

    if not my_leaves:

        st.info(
            "لسه ماعندكش أي إجازات مسجلة"
        )

    else:

        leaves_df = pd.DataFrame(my_leaves)

        # نعرض بس الأعمدة المهمة وبالترتيب المفهوم
        columns_order = [
            "نوع الإجازة",
            "عدد الأيام",
            "تاريخ البداية",
            "تاريخ العودة"
        ]

        existing_columns = [
            c for c in columns_order
            if c in leaves_df.columns
        ]

        leaves_df = leaves_df[existing_columns]

        # ترتيب من الأحدث للأقدم
        leaves_df = leaves_df.sort_values(
            by="تاريخ البداية",
            ascending=False
        )

        st.dataframe(
            leaves_df,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # ==================================
    # Leave Form
    # ==================================

    leave_type = st.selectbox(
        "نوع الإجازة",
        [
            "طارئة",
            "مخططة"
        ]
    )

    start_date = st.date_input(
        "تاريخ بداية الإجازة",
        value=date.today()
    )

    # ==================================
    # Emergency Leave
    # ==================================

    if leave_type == "طارئة":

        leave_days = 1

        return_date = (
            start_date +
            timedelta(days=1)
        )

        st.info(
            f"📅 تاريخ العودة: {return_date}"
        )

    # ==================================
    # Planned Leave
    # ==================================

    else:

        available_days = (
            get_available_planned_days(
                st.session_state.display_name
            )
        )

        if not available_days:

            st.error(
                "❌ لا يوجد رصيد إجازات مخططة متبقي"
            )

            return

        leave_days = st.selectbox(
            "عدد الأيام",
            available_days
        )

        return_date = (
            calculate_return_date(
                start_date,
                leave_days
            )
        )

        st.info(
            f"📅 تاريخ العودة: {return_date}"
        )

    # ==================================
    # Save Leave
    # ==================================

    if st.button(
        "📨 إرسال الطلب"
    ):

        # --------------------------
        # Emergency Validation
        # --------------------------

        if leave_type == "طارئة":

            if (
                stats[
                    "emergency_remaining"
                ] <= 0
            ):

                st.error(
                    "❌ استنفذت رصيد الإجازات الطارئة لهذا العام"
                )

                return

        # --------------------------
        # Planned Validation
        # --------------------------

        if leave_type == "مخططة":

            if (
                leave_days >
                stats[
                    "planned_monthly_remaining"
                ]
            ):

                st.error(
                    "❌ لا يوجد رصيد شهري كافٍ"
                )

                return

            if (
                leave_days >
                stats[
                    "planned_yearly_remaining"
                ]
            ):

                st.error(
                    "❌ لا يوجد رصيد سنوي كافٍ"
                )

                return

        # --------------------------
        # Save
        # --------------------------

        save_leave(
            employee_name=st.session_state.display_name,
            leave_type=leave_type,
            leave_days=leave_days,
            start_date=start_date,
            return_date=return_date
        )

        st.success(
            "تم تسجيل الإجازة بنجاح ✅"
        )

   

        st.rerun()