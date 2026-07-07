# ui/data_review_page.py

import streamlit as st
import pandas as pd

from datetime import date

from services.data_review_service import (
    load_platform_records,
    load_sheet_records,
    compare_records
)


def render_result_table(records):

    if not records:

        st.success("✅ لا يوجد اختلافات")

        return

    rows = [
        {
            "اسم الطالب": record["raw_name"],
            "رقم التليفون": record["raw_phone"],
            "اسم الموظف": record["raw_employee"]
        }
        for record in records
    ]

    dataframe = pd.DataFrame(rows)

    st.dataframe(
        dataframe,
        use_container_width=True,
        hide_index=True
    )


def render_data_review_page():

    st.title("🔍 مراجعة البيانات")

    st.caption(
        "رفع ملف الـ CSV اللي بينزل من المنصة، ومقارنته "
        "بالجوجل شيت لنفس التاريخ."
    )

    selected_date = st.date_input(
        "📅 التاريخ",
        value=date.today(),
        key="review_selected_date"
    )

    uploaded_file = st.file_uploader(
        "📤 رفع ملف CSV من المنصة",
        type=["csv"],
        key="review_csv_upload"
    )

    if uploaded_file is None:

        st.info("رفع ملف الـ CSV الأول عشان تقدر تعمل المقارنة")

        return

    if st.button("🔄 مقارنة البيانات"):

        platform_records = load_platform_records(
            uploaded_file
        )

        sheet_records = load_sheet_records(selected_date)

        missing_in_sheet, missing_in_platform = compare_records(
            platform_records,
            sheet_records
        )

        st.session_state["review_result"] = {
            "missing_in_sheet": missing_in_sheet,
            "missing_in_platform": missing_in_platform
        }

    result = st.session_state.get("review_result")

    if not result:
        return

    st.divider()

    st.subheader(
        "📥 موجود فى ملف المنصة وغير موجود فى الجوجل شيت"
    )

    render_result_table(result["missing_in_sheet"])

    st.divider()

    st.subheader(
        "📤 موجود فى الجوجل شيت وغير موجود فى ملف المنصة"
    )

    render_result_table(result["missing_in_platform"])