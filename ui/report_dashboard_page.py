# ui/report_dashboard_page.py

import streamlit as st
import pandas as pd

from datetime import date, timedelta

from services.report_service import (
    get_combined_records,
    get_unique_employees,
    build_stats
)


def render_counts_table(stats):

    st.markdown("#### 📋 جدول الأعداد")

    rows = [
        {"البيان": "عدد الطلاب", "القيمة": stats["total"]},
        {"البيان": "أولى ثانوي", "القيمة": stats["grade_1_count"]},
        {"البيان": "تالتة ثانوي", "القيمة": stats["grade_3_count"]},
    ]

    for status, count in stats["status_counts"].items():
        rows.append({"البيان": status, "القيمة": count})

    for note, count in stats["note_counts"].items():
        rows.append({"البيان": note, "القيمة": count})

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


def render_courses_table(title, courses_dict):

    st.markdown(f"#### 📚 {title}")

    if not courses_dict:

        st.info("لا يوجد كورسات مسجلة فى الفترة دي")

        return

    rows = []

    for course, data in courses_dict.items():

        rows.append({
            "الكورس": course,
            "عدد الطلاب": data["count"],
            "الإيرادات": data["price"]
        })

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


def render_totals_table(stats):

    st.markdown("#### 💰 الإجمالي")

    rows = [
        {"البيان": "أولى ثانوي", "القيمة": stats["g1_revenue"]},
        {"البيان": "تالتة ثانوي", "القيمة": stats["g3_revenue"]},
        {
            "البيان": "الإجمالي الكلي",
            "القيمة": stats["grand_total_revenue"]
        },
    ]

    df = pd.DataFrame(rows)

    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )


def render_report_dashboard():

    st.title("📝 Report")

    # ==================================
    # فلتر التاريخ
    # ==================================

    col1, col2 = st.columns(2)

    with col1:

        start_date = st.date_input(
            "من تاريخ",
            value=date.today() - timedelta(days=30),
            key="report_start_date"
        )

    with col2:

        end_date = st.date_input(
            "إلى تاريخ",
            value=date.today(),
            key="report_end_date"
        )

    if start_date > end_date:

        st.error("تاريخ البداية لازم يكون قبل تاريخ النهاية")

        return

    if st.button("📊 جلب البيانات"):

        st.session_state["report_records"] = get_combined_records(
            start_date=start_date,
            end_date=end_date
        )

    records = st.session_state.get("report_records")

    if records is None:

        st.info(
            "اختار الفترة واضغط على 'جلب البيانات' الأول"
        )

        return

    if not records:

        st.warning("مفيش أي بيانات فى الفترة المحددة")

        return

    # ==================================
    # اختيار الموظف
    # ==================================

    employees = get_unique_employees(records)

    selected_employee = st.selectbox(
        "👤 اختار الموظف",
        ["الكل"] + employees,
        key="report_selected_employee"
    )

    stats = build_stats(
        records,
        employee_filter=selected_employee
    )

    st.divider()

    render_counts_table(stats)

    st.divider()

    render_courses_table(
        "اشتراكات أولى ثانوي",
        stats["g1_courses"]
    )

    st.divider()

    render_courses_table(
        "اشتراكات 3 ثانوي",
        stats["g3_courses"]
    )

    st.divider()

    render_totals_table(stats)