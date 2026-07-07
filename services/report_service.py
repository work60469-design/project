# services/report_service.py

from datetime import datetime

from services.sheets_service import get_sheet


# الأعمدة الثابتة اللي مش كورسات (كل عمود تاني فى الشيت
# غيرها بيعتبر كورس تلقائيًا)
FIXED_COLUMNS = {
    "اسم الطالب",
    "رقم الطالب",
    "المحافظة",
    "الحالة",
    "الرقم اللى محول منه",
    "الصف",
    "الملاحظة",
    "سبب الملاحظة",
    "تاريخ التسجيل",
    "اسم الموظف"
}

SHEETS_TO_ANALYZE = ["Students 1", "Students 3"]


def _parse_date(date_str):

    date_str = str(date_str).strip()

    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return None


def _get_course_columns(headers):

    return [
        header for header in headers
        if header not in FIXED_COLUMNS
    ]


def get_combined_records(start_date=None, end_date=None):
    """
    بيرجع كل صفوف الطلاب من الشيتين ("Students 1" و "Students 3")
    مفلترة بتاريخ التسجيل (لو حددت start_date / end_date)، مع
    تحديد أعمدة الكورسات الحقيقية لكل شيت تلقائيًا من الهيدر.

    ده الفانكشن الوحيد اللي بيكلم جوجل شيتس هنا. بعد ما تجيب
    النتيجة مرة، استخدمها فى get_unique_employees و build_stats
    من غير ما تنادي الشيت تاني.
    """

    all_records = []

    for sheet_name in SHEETS_TO_ANALYZE:

        sheet = get_sheet(sheet_name)

        headers = sheet.row_values(1)

        course_columns = _get_course_columns(headers)

        rows = sheet.get_all_records()

        for row in rows:

            registration_date = _parse_date(
                row.get("تاريخ التسجيل", "")
            )

            if start_date and (
                not registration_date
                or registration_date < start_date
            ):
                continue

            if end_date and (
                not registration_date
                or registration_date > end_date
            ):
                continue

            row = dict(row)
            row["_sheet_name"] = sheet_name
            row["_course_columns"] = course_columns

            all_records.append(row)

    return all_records


def get_unique_employees(records):
    """
    بيرجع ليستة بكل أسماء الموظفين الموجودة فعليًا فى الريكوردز
    دي (من غير ما يكلم الشيت تاني).
    """

    names = set()

    for record in records:

        name = str(record.get("اسم الموظف", "")).strip()

        if name:
            names.add(name)

    return sorted(names)


def build_stats(records, employee_filter=None):
    """
    بيحسب كل الإحصائيات المطلوبة من ليستة ريكوردز جاهزة
    (من غير أي نداء تانى لجوجل شيتس). لو employee_filter
    محدد وموش "الكل"، بيحسب بس على الموظف ده.
    """

    if employee_filter and employee_filter != "الكل":

        records = [
            record for record in records
            if str(
                record.get("اسم الموظف", "")
            ).strip() == employee_filter
        ]

    # ترتيب الكورسات حسب ظهورها فى كل شيت (عشان تفضل
    # ديناميكية لو اتضاف كورس جديد)
    g1_courses_order = []
    g3_courses_order = []

    status_order = []
    note_order = []

    for record in records:

        sheet_name = record["_sheet_name"]

        target_order = (
            g1_courses_order
            if sheet_name == "Students 1"
            else g3_courses_order
        )

        for course in record["_course_columns"]:
            if course not in target_order:
                target_order.append(course)

        status = str(record.get("الحالة", "")).strip()

        if status and status not in status_order:
            status_order.append(status)

        note = str(record.get("الملاحظة", "")).strip()

        if note and note not in note_order:
            note_order.append(note)

    g1_courses = {
        course: {"count": 0, "price": 0.0}
        for course in g1_courses_order
    }

    g3_courses = {
        course: {"count": 0, "price": 0.0}
        for course in g3_courses_order
    }

    status_counts = {status: 0 for status in status_order}
    note_counts = {note: 0 for note in note_order}

    grade_1_count = 0
    grade_3_count = 0

    for record in records:

        grade = record.get("الصف", "")

        if grade == "أولى ثانوي":
            grade_1_count += 1
        else:
            grade_3_count += 1

        status = str(record.get("الحالة", "")).strip()

        if status:
            status_counts[status] += 1

        note = str(record.get("الملاحظة", "")).strip()

        if note:
            note_counts[note] += 1

        target_courses = (
            g1_courses
            if record["_sheet_name"] == "Students 1"
            else g3_courses
        )

        for course in record["_course_columns"]:

            value = str(record.get(course, "")).strip()

            if value == "":
                continue

            target_courses[course]["count"] += 1

            try:
                target_courses[course]["price"] += float(value)
            except ValueError:
                pass

    g1_revenue = sum(
        course_data["price"] for course_data in g1_courses.values()
    )

    g3_revenue = sum(
        course_data["price"] for course_data in g3_courses.values()
    )

    return {
        "total": len(records),
        "grade_1_count": grade_1_count,
        "grade_3_count": grade_3_count,
        "status_counts": status_counts,
        "note_counts": note_counts,
        "g1_courses": g1_courses,
        "g3_courses": g3_courses,
        "g1_revenue": g1_revenue,
        "g3_revenue": g3_revenue,
        "grand_total_revenue": g1_revenue + g3_revenue
    }