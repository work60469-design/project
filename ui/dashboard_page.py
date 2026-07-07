# ui/dashboard_page.py

import streamlit as st
import pandas as pd
import plotly.express as px
import io

from datetime import date

from services.dashboard_service import (
    get_today_stats,
    get_course_stats,
    get_student_completion_stats,
    get_student_status_stats,
    get_overall_totals,
    get_employee_overall_stats,
    get_followup_team_stats,
    get_registration_trend,
    get_daily_reports,
    get_withdrawn_students_stats,
    get_monthly_feedback_summary,
    get_break_dashboard_stats,
    _get_sheet_records
)

from services.leave_dashboard_service import (
    get_leave_dashboard_stats
)

from services.attendance_dashboard_service import (
    get_attendance_stats
)


def dataframe_to_excel_bytes(df, sheet_name="Sheet1"):
    """
    يحول DataFrame لملف Excel (bytes) جاهز للتحميل عن طريق
    st.download_button.
    """

    buffer = io.BytesIO()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)

    return buffer.getvalue()


def render_dashboard_page():

    st.title("📊 Dashboard")

    st.markdown(
        """
        <style>
        .dashboard-nav-wrapper {
            position: sticky;
            top: 10px;
            z-index: 9999;
            padding: 8px 10px;
            border-radius: 10px;
            background-color: rgba(128, 128, 128, 0.08);
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.25);
            margin-bottom: 10px;
        }

        .dashboard-nav {
            direction: rtl;
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }

        .dashboard-nav a {
            display: inline-block;
            padding: 6px 14px;
            border-radius: 20px;
            background-color: rgba(128, 128, 128, 0.15);
            color: inherit;
            text-decoration: none;
            font-size: 14px;
            white-space: nowrap;
        }

        .dashboard-nav a:hover {
            background-color: rgba(128, 128, 128, 0.30);
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown('<div class="dashboard-nav-wrapper">', unsafe_allow_html=True)

    nav_col_refresh, nav_col_links = st.columns([1, 4])

    with nav_col_refresh:

        if st.button("🔄 تحديث البيانات"):
            _get_sheet_records.clear()
            st.rerun()

    with nav_col_links:

        st.markdown(
            """
            <div class="dashboard-nav">
                <a href="#sec-today">📅 إحصائيات اليوم</a>
                <a href="#sec-courses">📚 تحليل الكورسات</a>
                <a href="#sec-employee">👥 الموظفين</a>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

    today_stats = get_today_stats()
    overall_totals = get_overall_totals()
    leave_stats = get_leave_dashboard_stats()
    attendance_stats = get_attendance_stats()

    # ==================================
    # 1) 📅 Today's Statistics
    # ==================================

    st.markdown('<div id="sec-today"></div>', unsafe_allow_html=True)
    st.subheader("📅 إحصائيات اليوم")

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.metric(
            "طلاب اليوم",
            today_stats["today_students"]
        )

    with c2:
        st.metric(
            "إيرادات اليوم",
            today_stats["today_revenue"]
        )

    with c3:
        st.metric(
            "أفضل موظف",
            today_stats["best_employee_today"] or "-"
        )

    with c4:
        st.metric(
            "أفضل كورس",
            today_stats["best_course_today"] or "-"
        )

    st.divider()

    # ==================================
    # 2) General KPI Cards (إجمالي الطلاب)
    # ==================================

    st.markdown('<div id="sec-totals"></div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "👨‍🎓 إجمالي الطلاب",
            overall_totals["total_students"]
        )

    with col2:
        st.metric(
            "💰 إجمالي الإيرادات",
            f"{overall_totals['total_revenue']} جنيه"
        )

    with col3:
        st.metric(
            "📈 متوسط الاشتراك",
            f"{overall_totals['average_revenue']} جنيه"
        )

    st.divider()

    # ==================================
    # 📈 نمو التسجيلات مع الوقت
    # ==================================

    st.markdown('<div id="sec-trend"></div>', unsafe_allow_html=True)
    st.subheader("📈 نمو التسجيلات مع الوقت")

    st.caption(
        "عدد التسجيلات (كل صف/تسجيل) فى كل يوم، مجمّعة من "
        "أولى ثانوي و3 ثانوي، عشان تشوف الاتجاه العام "
        "(بيزيد ولا بينقص) على مدار الفترة اللي تختارها."
    )

    trend_date_col1, trend_date_col2 = st.columns(2)

    with trend_date_col1:

        trend_start_date = st.date_input(
            "من تاريخ",
            value=date(2026, 7, 1),
            key="trend_stats_start"
        )

    with trend_date_col2:

        trend_end_date = st.date_input(
            "لحد تاريخ",
            value=date.today(),
            key="trend_stats_end"
        )

    trend_data = get_registration_trend(
        start_date=trend_start_date,
        end_date=trend_end_date
    )

    if not trend_data:

        st.info(
            "لا يوجد تسجيلات فى الفترة المختارة"
        )

    else:

        trend_df = pd.DataFrame(trend_data)

        fig_trend = px.line(
            trend_df,
            x="date",
            y="count",
            title="عدد التسجيلات يوميًا",
            markers=True,
            labels={
                "date": "التاريخ",
                "count": "عدد التسجيلات"
            }
        )
        st.plotly_chart(
            fig_trend,
            use_container_width=True,
            key="registration_trend_line"
        )

    st.divider()

    # ==================================
    # 3) 📚 تحليل الكورسات
    # ==================================

    st.markdown('<div id="sec-courses"></div>', unsafe_allow_html=True)
    st.subheader("📚 تحليل الكورسات")

    st.caption(
        "بيحسب كل تسجيل مستقل (لو نفس الطالب مسجل أكتر من مرة، "
        "كل تسجيل بيتحسب لوحده)."
    )

    date_col1, date_col2 = st.columns(2)

    with date_col1:

        course_start_date = st.date_input(
            "من تاريخ",
            value=date(2026, 7, 1),
            key="course_stats_start"
        )

    with date_col2:

        course_end_date = st.date_input(
            "لحد تاريخ",
            value=date.today(),
            key="course_stats_end"
        )

    course_stats_data = get_course_stats(
        start_date=course_start_date,
        end_date=course_end_date
    )

    def render_course_group(
        group_data, group_title, chart_key_prefix, compare_data=None
    ):

        st.markdown(f"#### {group_title}")

        gcol1, gcol2, gcol3 = st.columns(3)

        with gcol1:
            st.metric(
                "👨‍🎓 عدد التسجيلات الفعلية",
                group_data["actual_registrations"]
            )

        with gcol2:
            st.metric(
                "📚 إجمالي مرات الاشتراك فى الكورسات",
                group_data["total_course_enrollments"]
            )

        with gcol3:
            st.metric(
                "💰 الإيرادات",
                f"{group_data['total_revenue']} جنيه"
            )

        st.caption(
            "💡 الفرق بين الرقمين الأولين طبيعي: لو طالب مسجل "
            "فى كورسين فى نفس التسجيل، هيتحسب مرة واحدة فى "
            "\"عدد التسجيلات الفعلية\"، ومرتين فى \"مرات الاشتراك\" "
            "(مرة لكل كورس)."
        )

        # ----------------------------------
        # 🥧 Pie: نسبة كل كورس داخل المجموعة دي
        # ----------------------------------

        pie_counts = {
            course: count
            for course, count in group_data["course_counts"].items()
            if count > 0
        }

        if pie_counts:

            pie_df = pd.DataFrame({
                "الكورس": list(pie_counts.keys()),
                "عدد المشتركين": list(pie_counts.values())
            })

            fig_course_pie = px.pie(
                pie_df,
                names="الكورس",
                values="عدد المشتركين",
                title=f"نسبة كل كورس - {group_title}"
            )
            st.plotly_chart(
                fig_course_pie,
                use_container_width=True,
                key=f"{chart_key_prefix}_course_pie"
            )

        # ----------------------------------
        # 🥧 Pie: مقارنة أولى ثانوي مقابل 3 ثانوي
        # (بيظهر بس فى التاب المجمّع لما نمرر compare_data)
        # ----------------------------------

        if compare_data:

            compare_df = pd.DataFrame({
                "المجموعة": list(compare_data.keys()),
                "عدد التسجيلات": list(compare_data.values())
            })

            fig_compare_pie = px.pie(
                compare_df,
                names="المجموعة",
                values="عدد التسجيلات",
                title="نسبة أولى ثانوي مقابل 3 ثانوي"
            )
            st.plotly_chart(
                fig_compare_pie,
                use_container_width=True,
                key=f"{chart_key_prefix}_grade_compare_pie"
            )

        counts_df = pd.DataFrame({
            "الكورس": list(group_data["course_counts"].keys()),
            "عدد المشتركين": list(
                group_data["course_counts"].values()
            )
        }).sort_values(by="عدد المشتركين", ascending=False)

        fig_counts = px.bar(
            counts_df,
            x="الكورس",
            y="عدد المشتركين",
            title=f"عدد المشتركين فى كل كورس - {group_title}",
            text="عدد المشتركين"
        )
        st.plotly_chart(
            fig_counts,
            use_container_width=True,
            key=f"{chart_key_prefix}_counts"
        )

        revenue_df = pd.DataFrame({
            "الكورس": list(group_data["course_revenue"].keys()),
            "الإيرادات": list(
                group_data["course_revenue"].values()
            )
        }).sort_values(by="الإيرادات", ascending=False)

        fig_revenue = px.bar(
            revenue_df,
            x="الكورس",
            y="الإيرادات",
            title=f"إيرادات كل كورس - {group_title}",
            text="الإيرادات"
        )
        st.plotly_chart(
            fig_revenue,
            use_container_width=True,
            key=f"{chart_key_prefix}_revenue"
        )

        with st.expander(f"📋 جدول أرقام - {group_title}"):

            table_df = pd.DataFrame({
                "الكورس": list(group_data["course_counts"].keys()),
                "عدد المشتركين": list(
                    group_data["course_counts"].values()
                ),
                "الإيرادات": list(
                    group_data["course_revenue"].values()
                )
            }).sort_values(by="عدد المشتركين", ascending=False)

            st.dataframe(
                table_df,
                use_container_width=True,
                hide_index=True
            )

    tab1, tab2, tab3 = st.tabs([
        "🥇 أولى ثانوي",
        "🥈 3 ثانوي",
        "🔀 الاتنين مجمّعين"
    ])

    with tab1:

        render_course_group(
            course_stats_data["grade_1"],
            "أولى ثانوي",
            "grade1"
        )

    with tab2:

        render_course_group(
            course_stats_data["grade_3"],
            "3 ثانوي",
            "grade3"
        )

    with tab3:

        render_course_group(
            course_stats_data["combined"],
            "الاتنين مجمّعين",
            "combined",
            compare_data={
                "أولى ثانوي": course_stats_data[
                    "grade_1"
                ]["actual_registrations"],
                "3 ثانوي": course_stats_data[
                    "grade_3"
                ]["actual_registrations"]
            }
        )

    st.divider()

    # ==================================
    # 4) 🏷️ تحليل حالة الطلاب (النوع + الملاحظة + المحافظة)
    # ==================================

    st.markdown('<div id="sec-status"></div>', unsafe_allow_html=True)
    st.subheader("🏷️ تحليل حالة الطلاب")

    st.caption(
        "توزيع الطلاب حسب الحالة (جديد/قديم)، الملاحظة "
        "(مجاني/تخفيض/قسط/...)، والمحافظة — لكل مجموعة لوحدها."
    )

    status_date_col1, status_date_col2 = st.columns(2)

    with status_date_col1:

        status_start_date = st.date_input(
            "من تاريخ",
            value=date.today(),
            key="status_stats_start"
        )

    with status_date_col2:

        status_end_date = st.date_input(
            "لحد تاريخ",
            value=date.today(),
            key="status_stats_end"
        )

    status_stats = get_student_status_stats(
        start_date=status_start_date,
        end_date=status_end_date
    )

    def render_status_group(group_data, group_title, key_prefix):

        st.markdown(f"#### {group_title}")

        st.metric(
            "👨‍🎓 إجمالي الطلاب",
            group_data["total_students"]
        )

        status_df = pd.DataFrame([
            {"الحالة": k, "عدد الطلاب": v}
            for k, v in group_data["status_counts"].items()
            if v > 0
        ])

        notes_df = pd.DataFrame([
            {"الملاحظة": k, "عدد الطلاب": v}
            for k, v in group_data["notes_counts"].items()
            if v > 0
        ])

        scol1, scol2 = st.columns(2)

        with scol1:

            if not status_df.empty:

                fig_status = px.pie(
                    status_df,
                    names="الحالة",
                    values="عدد الطلاب",
                    title=f"جديد / قديم - {group_title}"
                )
                st.plotly_chart(
                    fig_status,
                    use_container_width=True,
                    key=f"{key_prefix}_status_pie"
                )

            else:

                st.info("لا يوجد بيانات كافية")

        with scol2:

            if not notes_df.empty:

                fig_notes = px.pie(
                    notes_df,
                    names="الملاحظة",
                    values="عدد الطلاب",
                    title=f"الملاحظات - {group_title}"
                )
                st.plotly_chart(
                    fig_notes,
                    use_container_width=True,
                    key=f"{key_prefix}_notes_pie"
                )

            else:

                st.info("لا يوجد بيانات كافية")

        governorate_df = pd.DataFrame({
            "المحافظة": list(group_data["governorate_counts"].keys()),
            "عدد الطلاب": list(group_data["governorate_counts"].values())
        }).sort_values(by="عدد الطلاب", ascending=False)

        fig_gov = px.bar(
            governorate_df,
            x="المحافظة",
            y="عدد الطلاب",
            title=f"توزيع الطلاب حسب المحافظة - {group_title}",
            text="عدد الطلاب"
        )
        st.plotly_chart(
            fig_gov,
            use_container_width=True,
            key=f"{key_prefix}_governorate_bar"
        )

        with st.expander(f"📋 جدول تفصيلي - {group_title}"):

            st.write("**الحالة (جديد/قديم):**")
            st.dataframe(
                status_df if not status_df.empty else pd.DataFrame(
                    {"الحالة": [], "عدد الطلاب": []}
                ),
                use_container_width=True,
                hide_index=True
            )

            st.write("**الملاحظة:**")
            st.dataframe(
                notes_df if not notes_df.empty else pd.DataFrame(
                    {"الملاحظة": [], "عدد الطلاب": []}
                ),
                use_container_width=True,
                hide_index=True
            )

            st.write("**المحافظات:**")
            st.dataframe(
                governorate_df,
                use_container_width=True,
                hide_index=True
            )

    status_tab1, status_tab2, status_tab3 = st.tabs([
        "🥇 أولى ثانوي",
        "🥈 3 ثانوي",
        "🔀 الاتنين مجمّعين"
    ])

    with status_tab1:

        render_status_group(
            status_stats["grade_1"],
            "أولى ثانوي",
            "status_grade1"
        )

    with status_tab2:

        render_status_group(
            status_stats["grade_3"],
            "3 ثانوي",
            "status_grade3"
        )

    with status_tab3:

        render_status_group(
            status_stats["combined"],
            "الاتنين مجمّعين",
            "status_combined"
        )

    st.divider()

    # ==================================
    # 🔙 الطلاب المنسحبين (سحب الاشتراك - استرداد الفلوس)
    # ==================================

    st.markdown('<div id="sec-withdrawn"></div>', unsafe_allow_html=True)
    st.subheader("🔙 الطلاب المنسحبين (سحب الاشتراك)")

    st.caption(
        "الطلاب اللي الملاحظة بتاعتهم \"سحب\" — يعني سحبوا "
        "اشتراكهم واسترد لهم الفلوس. المبلغ المسترد بيتحسب "
        "من قيم الكورسات فى نفس صف تسجيل الطالب."
    )

    withdrawn_date_col1, withdrawn_date_col2 = st.columns(2)

    with withdrawn_date_col1:

        withdrawn_start_date = st.date_input(
            "من تاريخ",
            value=date.today(),
            key="withdrawn_stats_start"
        )

    with withdrawn_date_col2:

        withdrawn_end_date = st.date_input(
            "لحد تاريخ",
            value=date.today(),
            key="withdrawn_stats_end"
        )

    withdrawn_stats = get_withdrawn_students_stats(
        start_date=withdrawn_start_date,
        end_date=withdrawn_end_date
    )

    def render_withdrawn_group(group_data, group_title, key_prefix):

        st.markdown(f"#### {group_title}")

        wcol1, wcol2 = st.columns(2)

        with wcol1:
            st.metric(
                "🔙 عدد المنسحبين",
                group_data["count"]
            )

        with wcol2:
            st.metric(
                "💸 إجمالي المبلغ المسترد",
                f"{group_data['total_refunded']} جنيه"
            )

        with st.expander(
            f"📋 قائمة المنسحبين - {group_title} "
            f"({group_data['count']} طالب)"
        ):

            if group_data["withdrawn_students"]:

                withdrawn_df = pd.DataFrame(
                    group_data["withdrawn_students"]
                )

                search_term = st.text_input(
                    "🔍 ابحث بالاسم أو رقم الطالب",
                    key=f"{key_prefix}_search"
                )

                if search_term.strip():

                    mask = (
                        withdrawn_df["اسم الطالب"].astype(str)
                        .str.contains(
                            search_term, case=False, na=False
                        )
                        |
                        withdrawn_df["رقم الطالب"].astype(str)
                        .str.contains(
                            search_term, case=False, na=False
                        )
                    )

                    filtered_df = withdrawn_df[mask]

                else:

                    filtered_df = withdrawn_df

                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True
                )

                excel_bytes = dataframe_to_excel_bytes(
                    filtered_df,
                    sheet_name="المنسحبين"
                )

                st.download_button(
                    "⬇️ تحميل Excel",
                    data=excel_bytes,
                    file_name=(
                        f"المنسحبين_{group_title}.xlsx"
                    ),
                    mime=(
                        "application/vnd.openxmlformats-"
                        "officedocument.spreadsheetml.sheet"
                    ),
                    key=f"{key_prefix}_download"
                )

            else:

                st.info("لا يوجد طلاب منسحبين حاليًا")

    withdrawn_tab1, withdrawn_tab2, withdrawn_tab3 = st.tabs([
        "🥇 أولى ثانوي",
        "🥈 3 ثانوي",
        "🔀 الاتنين مجمّعين"
    ])

    with withdrawn_tab1:

        render_withdrawn_group(
            withdrawn_stats["grade_1"],
            "أولى ثانوي",
            "withdrawn_grade1"
        )

    with withdrawn_tab2:

        render_withdrawn_group(
            withdrawn_stats["grade_3"],
            "3 ثانوي",
            "withdrawn_grade3"
        )

    with withdrawn_tab3:

        render_withdrawn_group(
            withdrawn_stats["combined"],
            "الاتنين مجمّعين",
            "withdrawn_combined"
        )

    st.divider()

    # ==================================
    # 5) 🔁 الطلاب المكمّلين (أكتر من كورس)
    # ==================================

    st.markdown('<div id="sec-completing"></div>', unsafe_allow_html=True)
    st.subheader("🔁 الطلاب المكمّلين")

    st.caption(
        "الطالب بيتحسب \"مكمل\" لو اشترك فى كورسين مختلفين "
        "أو أكتر عبر كل تسجيلاته (سواء دفعة واحدة أو على "
        "مدار الوقت). التحليل ده بشكل عام، مش مقيد بفترة معينة."
    )

    completion_stats = get_student_completion_stats()

    def render_completion_group(group_data, group_title, key_prefix):

        st.markdown(f"#### {group_title}")

        comp_col1, comp_col2, comp_col3 = st.columns(3)

        with comp_col1:
            st.metric(
                "👨‍🎓 إجمالي الطلاب",
                group_data["total_students"]
            )

        with comp_col2:
            st.metric(
                "🔁 الطلاب المكمّلين (كورسين فأكتر)",
                group_data["total_completing"]
            )

        with comp_col3:
            st.metric(
                "📊 نسبة الإكمال",
                f"{group_data['completion_rate']}%"
            )

        completion_counts = group_data["completion_counts"]

        distribution_df = pd.DataFrame({
            "عدد الكورسات": [
                f"{count} كورس"
                for count in completion_counts.keys()
            ],
            "عدد الطلاب": list(completion_counts.values()),
            "_ترتيب": list(completion_counts.keys())
        }).sort_values(by="_ترتيب")

        fig_completion = px.bar(
            distribution_df,
            x="عدد الكورسات",
            y="عدد الطلاب",
            title=f"توزيع الطلاب حسب عدد الكورسات - {group_title}",
            text="عدد الطلاب"
        )
        st.plotly_chart(
            fig_completion,
            use_container_width=True,
            key=f"{key_prefix}_completion_distribution"
        )

        with st.expander(
            f"📋 قائمة الطلاب المكمّلين - {group_title} "
            f"({group_data['total_completing']} طالب)"
        ):

            if group_data["completing_students"]:

                completing_df = pd.DataFrame(
                    group_data["completing_students"]
                )

                search_term = st.text_input(
                    "🔍 ابحث بالاسم أو رقم الطالب",
                    key=f"{key_prefix}_search"
                )

                if search_term.strip():

                    mask = (
                        completing_df["اسم الطالب"].astype(str)
                        .str.contains(
                            search_term, case=False, na=False
                        )
                        |
                        completing_df["رقم الطالب"].astype(str)
                        .str.contains(
                            search_term, case=False, na=False
                        )
                    )

                    filtered_df = completing_df[mask]

                else:

                    filtered_df = completing_df

                st.dataframe(
                    filtered_df,
                    use_container_width=True,
                    hide_index=True
                )

                excel_bytes = dataframe_to_excel_bytes(
                    filtered_df,
                    sheet_name="المكملين"
                )

                st.download_button(
                    "⬇️ تحميل Excel",
                    data=excel_bytes,
                    file_name=(
                        f"الطلاب_المكملين_{group_title}.xlsx"
                    ),
                    mime=(
                        "application/vnd.openxmlformats-"
                        "officedocument.spreadsheetml.sheet"
                    ),
                    key=f"{key_prefix}_download"
                )

            else:

                st.info(
                    "لا يوجد طلاب مكمّلين حاليًا"
                )

    comp_tab1, comp_tab2, comp_tab3 = st.tabs([
        "🥇 أولى ثانوي",
        "🥈 3 ثانوي",
        "🔀 الاتنين مجمّعين"
    ])

    with comp_tab1:

        render_completion_group(
            completion_stats["grade_1"],
            "أولى ثانوي",
            "comp_grade1"
        )

    with comp_tab2:

        render_completion_group(
            completion_stats["grade_3"],
            "3 ثانوي",
            "comp_grade3"
        )

    with comp_tab3:

        render_completion_group(
            completion_stats["combined"],
            "الاتنين مجمّعين",
            "comp_combined"
        )

    st.divider()

    # ==================================
    # 6) 👥 الطلاب حسب الموظف + 7) 💰 الإيرادات حسب الموظف
    # ==================================
    # ملحوظة: دلوقتي مربوطين بشيتات "Students 1" و "Students 3"
    # الصحيحة بدل شيت "Students" القديم، ومفلترين بتاريخ
    # تسجيل يختاره المستخدم (افتراضيًا: اليوم بس)

    st.markdown('<div id="sec-employee"></div>', unsafe_allow_html=True)
    st.subheader("👥💰 الطلاب والإيرادات حسب الموظف")

    emp_date_col1, emp_date_col2 = st.columns(2)

    with emp_date_col1:

        employee_start_date = st.date_input(
            "من تاريخ",
            value=date.today(),
            key="employee_stats_start"
        )

    with emp_date_col2:

        employee_end_date = st.date_input(
            "لحد تاريخ",
            value=date.today(),
            key="employee_stats_end"
        )

    employee_overall_stats = get_employee_overall_stats(
        start_date=employee_start_date,
        end_date=employee_end_date
    )

    st.markdown("#### 👥 الطلاب حسب الموظف")

    employee_df = pd.DataFrame({
        "الموظف": list(
            employee_overall_stats["employee_counts"].keys()
        ),
        "عدد الطلاب": list(
            employee_overall_stats["employee_counts"].values()
        )
    }).sort_values(by="عدد الطلاب", ascending=False)

    fig_employee = px.bar(
        employee_df,
        x="الموظف",
        y="عدد الطلاب",
        title="عدد الطلاب لكل موظف",
        text="عدد الطلاب"
    )
    st.plotly_chart(
        fig_employee,
        use_container_width=True,
        key="employee_students_bar"
    )

    st.markdown("#### 💰 الإيرادات حسب الموظف")

    revenue_df = pd.DataFrame({
        "الموظف": list(
            employee_overall_stats["employee_revenue"].keys()
        ),
        "الإيرادات": list(
            employee_overall_stats["employee_revenue"].values()
        )
    }).sort_values(by="الإيرادات", ascending=False)

    fig_revenue = px.bar(
        revenue_df,
        x="الموظف",
        y="الإيرادات",
        title="إيرادات كل موظف",
        text="الإيرادات"
    )
    st.plotly_chart(
        fig_revenue,
        use_container_width=True,
        key="employee_revenue_bar"
    )

    st.divider()

    # ==================================
    # 📞 فريق المتابعة (مكالمات/ردود)
    # ==================================

    st.markdown('<div id="sec-followup"></div>', unsafe_allow_html=True)
    st.subheader("📞 فريق المتابعة (مكالمات/ردود)")

    followup_date_col1, followup_date_col2 = st.columns(2)

    with followup_date_col1:

        followup_start_date = st.date_input(
            "من تاريخ",
            value=date.today(),
            key="followup_stats_start"
        )

    with followup_date_col2:

        followup_end_date = st.date_input(
            "لحد تاريخ",
            value=date.today(),
            key="followup_stats_end"
        )

    followup_stats = get_followup_team_stats(
        start_date=followup_start_date,
        end_date=followup_end_date
    )

    fcol1, fcol2 = st.columns(2)

    with fcol1:
        st.metric(
            "📞 إجمالي المكالمات",
            followup_stats["total_calls"]
        )

    with fcol2:
        st.metric(
            "💬 إجمالي الردود",
            followup_stats["total_responses"]
        )

    followup_df = pd.DataFrame({
        "الموظف": list(
            followup_stats["employee_calls"].keys()
        ),
        "عدد المكالمات": list(
            followup_stats["employee_calls"].values()
        ),
        "عدد الردود": [
            followup_stats["employee_responses"].get(emp, 0)
            for emp in followup_stats["employee_calls"]
        ],
        "متوسط التقييم": [
            followup_stats["employee_avg_rating"].get(emp, 0)
            for emp in followup_stats["employee_calls"]
        ]
    })

    fig_calls = px.bar(
        followup_df.sort_values(
            by="عدد المكالمات", ascending=False
        ),
        x="الموظف",
        y="عدد المكالمات",
        title="عدد المكالمات لكل موظف",
        text="عدد المكالمات"
    )
    st.plotly_chart(
        fig_calls,
        use_container_width=True,
        key="followup_calls_bar"
    )

    fig_responses = px.bar(
        followup_df.sort_values(
            by="عدد الردود", ascending=False
        ),
        x="الموظف",
        y="عدد الردود",
        title="عدد الطلاب الذين ردوا لكل موظف",
        text="عدد الردود"
    )
    st.plotly_chart(
        fig_responses,
        use_container_width=True,
        key="followup_responses_bar"
    )

    fig_rating = px.bar(
        followup_df.sort_values(
            by="متوسط التقييم", ascending=False
        ),
        x="الموظف",
        y="متوسط التقييم",
        title="متوسط التقييم لكل موظف",
        text="متوسط التقييم"
    )
    st.plotly_chart(
        fig_rating,
        use_container_width=True,
        key="followup_rating_bar"
    )

    # ----------------------------------
    # 🥧 Pie: نسبة اللي مش بيردوا مقابل المكالمات
    # (عام لكل الفريق، وبعدين سارة وملك كل واحدة لوحدها)
    # ----------------------------------

    st.markdown("#### 📵 نسبة عدم الرد مقابل المكالمات")

    def render_no_response_pie(calls, responses, title, key):

        if calls <= 0:

            st.info(
                f"لا يوجد مكالمات مسجّلة لـ {title}"
            )

            return

        not_responded = max(calls - responses, 0)
        responded = min(responses, calls)

        pie_df = pd.DataFrame({
            "الحالة": ["لم يردوا", "ردوا"],
            "العدد": [not_responded, responded]
        })

        fig = px.pie(
            pie_df,
            names="الحالة",
            values="العدد",
            title=title,
            color="الحالة",
            color_discrete_map={
                "لم يردوا": "#e74c3c",
                "ردوا": "#2ecc71"
            }
        )
        st.plotly_chart(
            fig,
            use_container_width=True,
            key=key
        )

    resp_col1, resp_col2, resp_col3 = st.columns(3)

    with resp_col1:

        render_no_response_pie(
            followup_stats["total_calls"],
            followup_stats["total_responses"],
            "عام - كل الفريق",
            "no_response_pie_overall"
        )

    with resp_col2:

        render_no_response_pie(
            followup_stats["employee_calls"].get("سارة", 0),
            followup_stats["employee_responses"].get("سارة", 0),
            "سارة",
            "no_response_pie_sara"
        )

    with resp_col3:

        render_no_response_pie(
            followup_stats["employee_calls"].get("ملك", 0),
            followup_stats["employee_responses"].get("ملك", 0),
            "ملك",
            "no_response_pie_malak"
        )

    with st.expander("📋 جدول تفصيلي - فريق المتابعة"):

        st.dataframe(
            followup_df.sort_values(
                by="عدد المكالمات", ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # ==================================
    # 📄 ملخص التقارير اليومي
    # ==================================

    st.markdown('<div id="sec-daily-reports"></div>', unsafe_allow_html=True)
    st.subheader("📄 ملخص التقارير اليومي")

    st.caption(
        "شوف تقارير كل الموظفين فى يوم واحد بس (من عمود "
        "\"التقرير\" فى شيت Feedback)."
    )

    report_date = st.date_input(
        "اليوم",
        value=date.today(),
        key="daily_report_date"
    )

    daily_reports = get_daily_reports(report_date)

    if not daily_reports:

        st.info(
            "لا يوجد تقارير مسجّلة فى هذا اليوم"
        )

    else:

        st.caption(
            f"عدد التقارير: {len(daily_reports)}"
        )

        for report in daily_reports:

            with st.container(border=True):

                rcol1, rcol2, rcol3, rcol4 = st.columns(4)

                with rcol1:
                    st.markdown(
                        f"**👤 {report['اسم الموظف']}**"
                    )

                with rcol2:
                    st.caption(
                        f"القسم: {report['القسم'] or '-'}"
                    )

                with rcol3:
                    st.caption(
                        f"📞 مكالمات: {report['عدد المكالمات'] or 0} | "
                        f"💬 ردود: {report['عدد الطلاب الذين ردوا'] or 0}"
                    )

                with rcol4:
                    st.caption(
                        f"⭐ تقييم: {report['التقييم'] or '-'} | "
                        f"{report['حالة الإرسال'] or '-'}"
                    )

                if str(report["التقرير"]).strip():

                    st.write(report["التقرير"])

                else:

                    st.caption("لا يوجد نص تقرير")

    st.divider()

    # ==================================================
    # 8) 👇 من هنا لتحت: كل حاجة خاصة بالموظفين
    # (الإجازات، البريك، الحضور، التأخير، متوسط ساعات العمل،
    # الحضور مقابل الغياب)
    # ==================================================
    # ملحوظة: قسمي "أفضل موظف/أعلى محافظة" و"ترتيب الموظفين"
    # اتشالوا من هنا (كانوا مبنيين على شيت "Students" القديم
    # الغلط، وكمان مكررين مع أقسام تانية مصلحة زي "الطلاب حسب
    # الموظف" و"تحليل حالة الطلاب").
    # ==================================================

    # ==================================
    # Leave Statistics
    # ==================================

    st.markdown('<div id="sec-leaves"></div>', unsafe_allow_html=True)
    st.subheader("🏖️ إحصائيات الإجازات")

    lc1, lc2, lc3, lc4 = st.columns(4)

    with lc1:
        st.metric(
            "إجمالي الإجازات",
            leave_stats["total_leaves"]
        )

    with lc2:
        st.metric(
            "الطارئة",
            leave_stats["emergency_count"]
        )

    with lc3:
        st.metric(
            "المخططة",
            leave_stats["planned_count"]
        )

    with lc4:
        st.metric(
            "أكثر موظف",
            leave_stats["top_employee"] or "-"
        )

    st.divider()

    # ==================================
    # ☕ تحليل البريك (شيفت الاستراحة) - مرتب تنازليًا
    # ==================================

    st.markdown('<div id="sec-breaks"></div>', unsafe_allow_html=True)
    st.subheader("☕ تحليل البريك")

    st.caption(
        "عدد مرات عمل شيفت البريك لكل موظف (افتراضي أو معدّل)، "
        "مرتبين تنازليًا حسب الإجمالي."
    )

    break_stats = get_break_dashboard_stats()

    if not break_stats["employee_ranking"]:

        st.info(
            "لا يوجد بيانات بريك مسجّلة حاليًا"
        )

    else:

        break_df = pd.DataFrame({
            "الموظف": [
                item[0] for item in break_stats["employee_ranking"]
            ],
            "إجمالي مرات البريك": [
                item[1] for item in break_stats["employee_ranking"]
            ],
            "الميعاد الافتراضي": [
                break_stats["default_breaks"].get(item[0], 0)
                for item in break_stats["employee_ranking"]
            ],
            "معدّل": [
                break_stats["changed_breaks"].get(item[0], 0)
                for item in break_stats["employee_ranking"]
            ]
        })

        fig_breaks = px.bar(
            break_df,
            x="الموظف",
            y="إجمالي مرات البريك",
            title="إجمالي مرات عمل شيفت البريك لكل موظف",
            text="إجمالي مرات البريك"
        )
        st.plotly_chart(
            fig_breaks,
            use_container_width=True,
            key="breaks_total_bar"
        )

        st.markdown("#### 🏆 ترتيب الموظفين (تنازلي)")

        break_medals = ["🥇", "🥈", "🥉"]

        for index, item in enumerate(
            break_stats["employee_ranking"]
        ):

            employee_name = item[0]
            total_count = item[1]

            default_count = break_stats["default_breaks"].get(
                employee_name, 0
            )
            changed_count = break_stats["changed_breaks"].get(
                employee_name, 0
            )

            medal = break_medals[index] if index < 3 else "🏅"

            st.write(
                f"{medal} {employee_name} — "
                f"{total_count} مرة"
            )
            st.caption(
                f"⏰ افتراضي: {default_count} | "
                f"🔁 معدّل: {changed_count}"
            )

        with st.expander("📋 جدول تفصيلي - تحليل البريك"):

            st.dataframe(
                break_df,
                use_container_width=True,
                hide_index=True
            )

    st.divider()

    # ==================================
    # Attendance Charts
    # ==================================

    st.markdown('<div id="sec-attendance"></div>', unsafe_allow_html=True)
    st.subheader("🕒 الحضور")

    attendance_df = pd.DataFrame({
        "الموظف": list(attendance_stats["attendance"].keys()),
        "عدد أيام الحضور": list(attendance_stats["attendance"].values())
    })

    fig_attendance = px.bar(
        attendance_df,
        x="الموظف",
        y="عدد أيام الحضور",
        title="عدد أيام الحضور لكل موظف"
    )
    st.plotly_chart(fig_attendance, use_container_width=True)

    st.markdown('<div id="sec-late"></div>', unsafe_allow_html=True)
    st.subheader("⏰ التأخير")

    late_df = pd.DataFrame({
        "الموظف": list(attendance_stats["late"].keys()),
        "مرات التأخير": list(attendance_stats["late"].values())
    })

    fig_late = px.bar(
        late_df,
        x="الموظف",
        y="مرات التأخير",
        title="عدد مرات التأخير لكل موظف"
    )
    st.plotly_chart(fig_late, use_container_width=True)

    st.markdown('<div id="sec-hours"></div>', unsafe_allow_html=True)
    st.subheader("⌛ متوسط ساعات العمل")

    hours_df = pd.DataFrame({
        "الموظف": list(attendance_stats["average_hours"].keys()),
        "متوسط الساعات": list(attendance_stats["average_hours"].values())
    })

    fig_hours = px.bar(
        hours_df,
        x="الموظف",
        y="متوسط الساعات",
        title="متوسط ساعات العمل"
    )
    st.plotly_chart(fig_hours, use_container_width=True)

    st.divider()

    # ==================================
    # Attendance vs Absence
    # ==================================

    st.markdown('<div id="sec-att-vs-abs"></div>', unsafe_allow_html=True)
    st.subheader("🟢 الحضور مقابل الغياب")

    attendance_vs_absence = []

    for employee in attendance_stats["attendance"]:
        attendance_vs_absence.append({
            "الموظف": employee,
            "النوع": "حضور",
            "القيمة": attendance_stats["attendance"][employee]
        })

        attendance_vs_absence.append({
            "الموظف": employee,
            "النوع": "غياب",
            "القيمة": attendance_stats["absence"][employee]
        })

    comparison_df = pd.DataFrame(attendance_vs_absence)

    fig_comparison = px.bar(
        comparison_df,
        x="الموظف",
        y="القيمة",
        color="النوع",
        barmode="group",
        title="الحضور مقابل الغياب"
    )
    st.plotly_chart(fig_comparison, use_container_width=True)

    st.divider()

    # ==================================
    # 📆 ملخص فريق المتابعة الشهري (عدد التقارير + التأخير)
    # ==================================

    st.markdown('<div id="sec-monthly-followup"></div>', unsafe_allow_html=True)
    st.subheader("📆 ملخص الفيدباك الشهري (كل الموظفين)")

    st.caption(
        "اختار أي يوم فى الشهر اللي عايز تشوفه (افتراضيًا "
        "النهارده)، وهيتحسب تلقائيًا كل الشهر لكل الموظفين "
        "(دعم فني، سوشيال، متابعة): كل موظف عمل تقرير كام مرة، "
        "وكام مرة كانت حالة الإرسال \"متأخر\"."
    )

    monthly_reference_date = st.date_input(
        "اختار يوم من الشهر المطلوب",
        value=date.today(),
        key="followup_monthly_reference_date"
    )

    monthly_summary = get_monthly_feedback_summary(
        monthly_reference_date
    )

    st.caption(
        f"الشهر المعروض: من {monthly_summary['month_start']} "
        f"لحد {monthly_summary['month_end']}"
    )

    if not monthly_summary["employee_reports_count"]:

        st.info("لا يوجد تقارير مسجّلة فى هذا الشهر")

    else:

        monthly_df = pd.DataFrame({
            "الموظف": list(
                monthly_summary["employee_reports_count"].keys()
            ),
            "عدد مرات التقرير": list(
                monthly_summary["employee_reports_count"].values()
            ),
            "عدد مرات التأخير": [
                monthly_summary["employee_late_count"].get(emp, 0)
                for emp in monthly_summary["employee_reports_count"]
            ]
        })

        fig_monthly_reports = px.bar(
            monthly_df.sort_values(
                by="عدد مرات التقرير", ascending=False
            ),
            x="الموظف",
            y="عدد مرات التقرير",
            title="عدد مرات التقرير لكل موظف خلال الشهر",
            text="عدد مرات التقرير"
        )
        st.plotly_chart(
            fig_monthly_reports,
            use_container_width=True,
            key="monthly_reports_bar"
        )

        fig_monthly_late = px.bar(
            monthly_df.sort_values(
                by="عدد مرات التأخير", ascending=False
            ),
            x="الموظف",
            y="عدد مرات التأخير",
            title="عدد مرات التأخير فى الإرسال لكل موظف خلال الشهر",
            text="عدد مرات التأخير"
        )
        st.plotly_chart(
            fig_monthly_late,
            use_container_width=True,
            key="monthly_late_bar"
        )

        with st.expander("📋 جدول تفصيلي - الملخص الشهري"):

            st.dataframe(
                monthly_df.sort_values(
                    by="عدد مرات التقرير", ascending=False
                ),
                use_container_width=True,
                hide_index=True
            )

            st.write(
                "**تفاصيل حالات الإرسال لكل موظف "
                "(كل القيم كما هي فى الشيت):**"
            )

            status_breakdown_rows = []

            for employee, status_counts in (
                monthly_summary["employee_status_counts"].items()
            ):

                for status_value, count in status_counts.items():

                    status_breakdown_rows.append({
                        "الموظف": employee,
                        "حالة الإرسال": status_value,
                        "عدد المرات": count
                    })

            if status_breakdown_rows:

                st.dataframe(
                    pd.DataFrame(status_breakdown_rows),
                    use_container_width=True,
                    hide_index=True
                )