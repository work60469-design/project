# services/dashboard_service.py

import streamlit as st

from services.sheets_service import get_sheet
from datetime import datetime, date
import calendar


# ==================================
# 🧊 كاش لقراءة الشيتات (يمنع 429 Quota exceeded)
# ==================================
# الصفحة بتنادي على نفس الشيتات ("Students 1"، "Students 3"،
# "Feedback"، ...) فى أكتر من فانكشن فى نفس اللحظة (تحليل
# الكورسات، الحالة، الإكمال، الموظفين، فريق المتابعة، ...).
# من غير كاش، كل ده كان بيعمل عشرات الطلبات لجوجل شيتس فى نفس
# الثانية وبيضرب الـ Quota (429). الكاش ده بيخزن نتيجة قراءة كل
# شيت لمدة 60 ثانية، فكل الفانكشنز اللي بتحتاج نفس الشيت فى
# نفس اللحظة تستخدم نفس النتيجة من غير طلب جديد لجوجل.

@st.cache_data(ttl=60, show_spinner=False)
def _get_sheet_records(sheet_name):

    sheet = get_sheet(sheet_name)

    return sheet.get_all_records()


COURSES_GRADE_1 = [
    "الترم كامل",
    "شهر 8",
    "شهر 9",
    "شهر 10",
    "شهر 11",
    "شهر 12",
    "شهر 1"
]

COURSES_GRADE_3 = [
    "السنوى",
    "الدعامة والحركة",
    "التنسيق الهرمونى",
    "التكاثر",
    "المناعة",
    "DNA & RNA"
]


def _parse_date_safe(date_text):

    try:
        return datetime.strptime(
            str(date_text).strip(),
            "%Y-%m-%d"
        ).date()

    except (ValueError, TypeError):
        return None


def _compute_stats_for_sheet(sheet_name, courses, start_date, end_date):
    """
    يحسب عدد المشتركين والإيرادات لكل كورس فى شيت واحد بس،
    مفلترة على تاريخ التسجيل لو محدد.

    كمان بيحسب "عدد التسجيلات الفعلية" = عدد الصفوف الحقيقية
    (كل صف بيتحسب مرة واحدة بس، حتى لو مشترك فى أكتر من كورس).
    """

    course_counts = {course: 0 for course in courses}
    course_revenue = {course: 0 for course in courses}

    actual_registrations = 0

    records = _get_sheet_records(sheet_name)

    for record in records:

        registration_date = _parse_date_safe(
            record.get("تاريخ التسجيل", "")
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

        # عدد الصفوف الفعلية (بغض النظر عن عدد الكورسات فى الصف)
        actual_registrations += 1

        for course in courses:

            value = record.get(course, "")

            # لو الخانة فاضية خالص، يعني الكورس ده مش مختار أصلا
            if str(value).strip() == "":
                continue

            try:
                price = int(value)
            except (ValueError, TypeError):
                price = 0

            # الطالب بيتحسب "مشترك" حتى لو مجاني (سعر = 0)
            course_counts[course] += 1
            course_revenue[course] += price

    total_course_enrollments = sum(course_counts.values())
    total_revenue = sum(course_revenue.values())

    return {
        "course_counts": course_counts,
        "course_revenue": course_revenue,
        "actual_registrations": actual_registrations,
        "total_course_enrollments": total_course_enrollments,
        "total_revenue": total_revenue
    }


def _normalize_phone(phone):

    phone = str(phone).strip()

    if phone.isdigit() and len(phone) == 10:
        phone = "0" + phone

    return phone


def _compute_completion_for_sheet(sheet_name, courses):
    """
    يرجع لكل رقم موبايل فى شيت واحد: كل الكورسات المختلفة
    اللي الطالب اشترك فيها، واسمه.
    """

    students_courses = {}
    students_names = {}

    records = _get_sheet_records(sheet_name)

    for record in records:

        phone = _normalize_phone(
            record.get("رقم الطالب", "")
        )

        if not phone:
            continue

        students_names[phone] = record.get(
            "اسم الطالب", ""
        )

        enrolled_courses = students_courses.setdefault(
            phone, set()
        )

        for course in courses:

            value = record.get(course, "")

            if str(value).strip() != "":
                enrolled_courses.add(course)

    return students_courses, students_names


def _build_completion_result(students_courses, students_names):
    """
    ياخد dict (رقم موبايل -> Set كورسات) ويرجع تحليل
    الإكمال الجاهز (كارتات، توزيع، ليستة المكمّلين).
    """

    completion_counts = {}
    completing_students = []

    for phone, courses_set in students_courses.items():

        courses_count = len(courses_set)

        completion_counts[courses_count] = (
            completion_counts.get(courses_count, 0) + 1
        )

        if courses_count >= 2:

            completing_students.append({
                "اسم الطالب": students_names.get(phone, ""),
                "رقم الطالب": phone,
                "عدد الكورسات": courses_count,
                "الكورسات": "، ".join(sorted(courses_set))
            })

    completing_students.sort(
        key=lambda item: item["عدد الكورسات"],
        reverse=True
    )

    total_students = len(students_courses)
    total_completing = len(completing_students)

    completion_rate = 0

    if total_students > 0:

        completion_rate = round(
            (total_completing / total_students) * 100,
            1
        )

    return {
        "total_students": total_students,
        "total_completing": total_completing,
        "completion_rate": completion_rate,
        "completion_counts": completion_counts,
        "completing_students": completing_students
    }


def get_student_completion_stats():
    """
    يرجع تحليل الطلاب المكمّلين فى 3 مجموعات منفصلة:
    - grade_1: أولى ثانوي لوحدها (كورساتها بس)
    - grade_3: 3 ثانوي لوحدها (كورساتها بس)
    - combined: الاتنين مجمّعين (لو نفس رقم الموبايل ظهر
      فى الشيتين، بيتجمع له كل الكورسات من الاتنين)

    مش مفلترة بتاريخ عمدًا، لأن الهدف تتبع سلوك الطالب على
    المدى الطويل مش فترة محددة.
    """

    grade_1_courses, grade_1_names = _compute_completion_for_sheet(
        "Students 1",
        COURSES_GRADE_1
    )

    grade_3_courses, grade_3_names = _compute_completion_for_sheet(
        "Students 3",
        COURSES_GRADE_3
    )

    grade_1_result = _build_completion_result(
        grade_1_courses,
        grade_1_names
    )

    grade_3_result = _build_completion_result(
        grade_3_courses,
        grade_3_names
    )

    # للمجمّع: بندمج كورسات نفس رقم الموبايل لو ظهر فى الشيتين
    combined_courses = {}
    combined_names = {}

    for phone, courses_set in grade_1_courses.items():

        combined_courses.setdefault(phone, set()).update(
            courses_set
        )
        combined_names[phone] = grade_1_names[phone]

    for phone, courses_set in grade_3_courses.items():

        combined_courses.setdefault(phone, set()).update(
            courses_set
        )
        combined_names[phone] = grade_3_names[phone]

    combined_result = _build_completion_result(
        combined_courses,
        combined_names
    )

    return {
        "grade_1": grade_1_result,
        "grade_3": grade_3_result,
        "combined": combined_result
    }


def get_course_stats(start_date=None, end_date=None):
    """
    يرجع تحليل الكورسات فى 3 مجموعات منفصلة:
    - grade_1: أولى ثانوي لوحدها (Students 1)
    - grade_3: 3 ثانوي لوحدها (Students 3)
    - combined: الاتنين مجمّعين مع بعض

    كل مجموعة فيها: course_counts, course_revenue,
    actual_registrations, total_course_enrollments, total_revenue.

    كل صف/تسجيل بيتحسب مستقل (لو نفس رقم الطالب مسجل أكتر
    من مرة، كل تسجيل يتحسب لوحده).
    """

    grade_1_stats = _compute_stats_for_sheet(
        "Students 1",
        COURSES_GRADE_1,
        start_date,
        end_date
    )

    grade_3_stats = _compute_stats_for_sheet(
        "Students 3",
        COURSES_GRADE_3,
        start_date,
        end_date
    )

    combined_course_counts = {
        **grade_1_stats["course_counts"],
        **grade_3_stats["course_counts"]
    }

    combined_course_revenue = {
        **grade_1_stats["course_revenue"],
        **grade_3_stats["course_revenue"]
    }

    combined_stats = {
        "course_counts": combined_course_counts,
        "course_revenue": combined_course_revenue,
        "actual_registrations": (
            grade_1_stats["actual_registrations"]
            + grade_3_stats["actual_registrations"]
        ),
        "total_course_enrollments": (
            grade_1_stats["total_course_enrollments"]
            + grade_3_stats["total_course_enrollments"]
        ),
        "total_revenue": (
            grade_1_stats["total_revenue"]
            + grade_3_stats["total_revenue"]
        )
    }

    return {
        "grade_1": grade_1_stats,
        "grade_3": grade_3_stats,
        "combined": combined_stats
    }


# ==================================
# 🏷️ تحليل حالة الطلاب (الحالة / الملاحظة / المحافظة)
# ==================================
# أسماء الأعمدة الحقيقية فى شيتات "Students 1" و "Students 3"
# لو الاسم اتغير فى الشيت، غيّره من هنا بس

STATUS_FIELD = "الحالة"
NOTES_FIELD = "الملاحظة"
GOVERNORATE_FIELD = "المحافظة"

STATUS_VALUES_OF_INTEREST = ["جديد", "قديم"]

NOTES_VALUES_OF_INTEREST = [
    "لا يوجد",
    "تخفيض",
    "مجاني",
    "قسط",
    "سحب",
    "حصة",
    "حصتين",
    "أخرى"
]


def _compute_categorical_stats_for_sheet(
    sheet_name, start_date=None, end_date=None
):
    """
    يحسب توزيع الطلاب فى شيت واحد بس حسب:
    - الحالة (جديد / قديم)
    - الملاحظة (لا يوجد / تخفيض / مجاني / قسط / سحب / حصة / حصتين / أخرى)
    - المحافظة

    مفلترة على تاريخ التسجيل لو محدد. كل صف بيتحسب مرة واحدة
    (بغض النظر عن عدد الكورسات فيه).
    """

    status_counts = {
        status: 0 for status in STATUS_VALUES_OF_INTEREST
    }
    notes_counts = {
        note: 0 for note in NOTES_VALUES_OF_INTEREST
    }
    governorate_counts = {}

    records = _get_sheet_records(sheet_name)

    total_students = 0

    for record in records:

        registration_date = _parse_date_safe(
            record.get("تاريخ التسجيل", "")
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

        total_students += 1

        status_value = str(
            record.get(STATUS_FIELD, "")
        ).strip()

        if status_value in status_counts:
            status_counts[status_value] += 1

        notes_value = str(
            record.get(NOTES_FIELD, "")
        ).strip()

        if notes_value in notes_counts:
            notes_counts[notes_value] += 1

        governorate_value = record.get(
            GOVERNORATE_FIELD, "غير محدد"
        )

        if str(governorate_value).strip() == "":
            governorate_value = "غير محدد"

        governorate_counts[governorate_value] = (
            governorate_counts.get(governorate_value, 0) + 1
        )

    return {
        "status_counts": status_counts,
        "notes_counts": notes_counts,
        "governorate_counts": governorate_counts,
        "total_students": total_students
    }


def get_student_status_stats(start_date=None, end_date=None):
    """
    يرجع توزيع الطلاب حسب الحالة/الملاحظة/المحافظة فى 3 مجموعات
    منفصلة (بنفس طريقة get_course_stats)، مفلترة على تاريخ
    التسجيل لو محدد:
    - grade_1: أولى ثانوي لوحدها (Students 1)
    - grade_3: 3 ثانوي لوحدها (Students 3)
    - combined: الاتنين مجمّعين
    """

    grade_1_stats = _compute_categorical_stats_for_sheet(
        "Students 1", start_date, end_date
    )

    grade_3_stats = _compute_categorical_stats_for_sheet(
        "Students 3", start_date, end_date
    )

    combined_status_counts = {
        status: (
            grade_1_stats["status_counts"][status]
            + grade_3_stats["status_counts"][status]
        )
        for status in STATUS_VALUES_OF_INTEREST
    }

    combined_notes_counts = {
        note: (
            grade_1_stats["notes_counts"][note]
            + grade_3_stats["notes_counts"][note]
        )
        for note in NOTES_VALUES_OF_INTEREST
    }

    combined_governorate_counts = {}

    for governorate, count in grade_1_stats["governorate_counts"].items():
        combined_governorate_counts[governorate] = (
            combined_governorate_counts.get(governorate, 0) + count
        )

    for governorate, count in grade_3_stats["governorate_counts"].items():
        combined_governorate_counts[governorate] = (
            combined_governorate_counts.get(governorate, 0) + count
        )

    combined_total = (
        grade_1_stats["total_students"]
        + grade_3_stats["total_students"]
    )

    return {
        "grade_1": grade_1_stats,
        "grade_3": grade_3_stats,
        "combined": {
            "status_counts": combined_status_counts,
            "notes_counts": combined_notes_counts,
            "governorate_counts": combined_governorate_counts,
            "total_students": combined_total
        }
    }


def _compute_withdrawn_for_sheet(
    sheet_name, courses, start_date=None, end_date=None
):
    """
    يلاقي كل الصفوف اللي "الملاحظة" فيها = "سحب" (يعني الطالب
    سحب اشتراكه واسترد فلوسه)، ويحسب المبلغ المسترد لكل صف
    (مجموع قيم الكورسات فى نفس الصف)، مفلترة على تاريخ التسجيل
    لو محدد.
    """

    records = _get_sheet_records(sheet_name)

    withdrawn_students = []
    total_refunded = 0

    for record in records:

        notes_value = str(
            record.get(NOTES_FIELD, "")
        ).strip()

        if notes_value != "سحب":
            continue

        registration_date = _parse_date_safe(
            record.get("تاريخ التسجيل", "")
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

        row_refund = 0

        for course in courses:

            value = record.get(course, "")

            if str(value).strip() == "":
                continue

            try:
                price = int(value)
            except (ValueError, TypeError):
                price = 0

            row_refund += price

        total_refunded += row_refund

        withdrawn_students.append({
            "اسم الطالب": record.get("اسم الطالب", ""),
            "رقم الطالب": record.get("رقم الطالب", ""),
            "المحافظة": record.get(GOVERNORATE_FIELD, ""),
            "سبب الملاحظة": record.get("سبب الملاحظة", ""),
            "المبلغ المسترد": row_refund,
            "تاريخ التسجيل": record.get("تاريخ التسجيل", ""),
            "اسم الموظف": record.get("اسم الموظف", "")
        })

    return withdrawn_students, total_refunded


def get_withdrawn_students_stats(start_date=None, end_date=None):
    """
    يرجع تحليل الطلاب اللي "سحبوا" اشتراكهم واسترد لهم فلوسهم،
    فى 3 مجموعات منفصلة (زي باقي التحليلات)، مفلترة على تاريخ
    التسجيل لو محدد:
    - grade_1: أولى ثانوي لوحدها
    - grade_3: 3 ثانوي لوحدها
    - combined: الاتنين مجمّعين
    """

    grade_1_list, grade_1_refund = _compute_withdrawn_for_sheet(
        "Students 1", COURSES_GRADE_1, start_date, end_date
    )

    grade_3_list, grade_3_refund = _compute_withdrawn_for_sheet(
        "Students 3", COURSES_GRADE_3, start_date, end_date
    )

    combined_list = grade_1_list + grade_3_list
    combined_refund = grade_1_refund + grade_3_refund

    return {
        "grade_1": {
            "withdrawn_students": grade_1_list,
            "count": len(grade_1_list),
            "total_refunded": grade_1_refund
        },
        "grade_3": {
            "withdrawn_students": grade_3_list,
            "count": len(grade_3_list),
            "total_refunded": grade_3_refund
        },
        "combined": {
            "withdrawn_students": combined_list,
            "count": len(combined_list),
            "total_refunded": combined_refund
        }
    }


def _compute_today_stats_for_sheet(sheet_name, courses, today):

    records = _get_sheet_records(sheet_name)

    students_today = 0
    revenue_today = 0
    employee_counts = {}
    course_counts = {}

    for record in records:

        registration_date = _parse_date_safe(
            record.get("تاريخ التسجيل", "")
        )

        if registration_date != today:
            continue

        students_today += 1

        employee = record.get(
            "اسم الموظف", "غير محدد"
        )

        employee_counts[employee] = (
            employee_counts.get(employee, 0) + 1
        )

        for course in courses:

            value = record.get(course, "")

            if str(value).strip() == "":
                continue

            try:
                price = int(value)
            except (ValueError, TypeError):
                price = 0

            revenue_today += price

            course_counts[course] = (
                course_counts.get(course, 0) + 1
            )

    return {
        "students_today": students_today,
        "revenue_today": revenue_today,
        "employee_counts": employee_counts,
        "course_counts": course_counts
    }


def get_overall_totals():
    """
    الإجمالي الكلي (طلاب / إيرادات / متوسط) من شيتات
    "Students 1" و "Students 3" مجمّعين، من غير فلترة تاريخ.
    """

    grade_1_stats = _compute_stats_for_sheet(
        "Students 1", COURSES_GRADE_1, None, None
    )

    grade_3_stats = _compute_stats_for_sheet(
        "Students 3", COURSES_GRADE_3, None, None
    )

    total_students = (
        grade_1_stats["actual_registrations"]
        + grade_3_stats["actual_registrations"]
    )

    total_revenue = (
        grade_1_stats["total_revenue"]
        + grade_3_stats["total_revenue"]
    )

    average_revenue = 0

    if total_students > 0:
        average_revenue = round(
            total_revenue / total_students, 2
        )

    return {
        "total_students": total_students,
        "total_revenue": total_revenue,
        "average_revenue": average_revenue
    }


def _compute_employee_stats_for_sheet(
    sheet_name, courses, start_date=None, end_date=None
):
    """
    يحسب لكل موظف: عدد التسجيلات (كل صف بيتحسب مرة واحدة)
    وإجمالي الإيرادات (مجموع كل الكورسات فى الصف) فى شيت واحد بس،
    مفلترة على تاريخ التسجيل لو محدد.
    """

    records = _get_sheet_records(sheet_name)

    employee_counts = {}
    employee_revenue = {}

    for record in records:

        registration_date = _parse_date_safe(
            record.get("تاريخ التسجيل", "")
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

        employee = record.get(
            "اسم الموظف", "غير محدد"
        )

        if str(employee).strip() == "":
            employee = "غير محدد"

        employee_counts[employee] = (
            employee_counts.get(employee, 0) + 1
        )

        row_revenue = 0

        for course in courses:

            value = record.get(course, "")

            if str(value).strip() == "":
                continue

            try:
                price = int(value)
            except (ValueError, TypeError):
                price = 0

            row_revenue += price

        employee_revenue[employee] = (
            employee_revenue.get(employee, 0) + row_revenue
        )

    return employee_counts, employee_revenue


def get_employee_overall_stats(start_date=None, end_date=None):
    """
    عدد الطلاب وإيرادات كل موظف، مجمّعة من شيتات
    "Students 1" و "Students 3" (بدل شيت "Students" القديم)،
    مفلترة على تاريخ التسجيل لو محدد.
    """

    grade_1_counts, grade_1_revenue = _compute_employee_stats_for_sheet(
        "Students 1", COURSES_GRADE_1, start_date, end_date
    )

    grade_3_counts, grade_3_revenue = _compute_employee_stats_for_sheet(
        "Students 3", COURSES_GRADE_3, start_date, end_date
    )

    combined_counts = {}
    combined_revenue = {}

    for employee, count in grade_1_counts.items():
        combined_counts[employee] = (
            combined_counts.get(employee, 0) + count
        )

    for employee, count in grade_3_counts.items():
        combined_counts[employee] = (
            combined_counts.get(employee, 0) + count
        )

    for employee, revenue in grade_1_revenue.items():
        combined_revenue[employee] = (
            combined_revenue.get(employee, 0) + revenue
        )

    for employee, revenue in grade_3_revenue.items():
        combined_revenue[employee] = (
            combined_revenue.get(employee, 0) + revenue
        )

    return {
        "employee_counts": combined_counts,
        "employee_revenue": combined_revenue
    }


# فريق المتابعة الحالي - أي تعديل فى الأعضاء يتم من هنا بس
FOLLOWUP_TEAM_MEMBERS = ["ملك", "سارة"]


def get_followup_team_stats(start_date=None, end_date=None):
    """
    تحليل فريق المتابعة (مكالمات/ردود) من شيت "Feedback"،
    مفلتر على "التاريخ" لو محدد، وعلى أعضاء فريق المتابعة
    الحاليين بس (FOLLOWUP_TEAM_MEMBERS). لكل موظف: إجمالي
    المكالمات، عدد الطلاب اللي ردوا، ومتوسط التقييم.
    """

    records = _get_sheet_records("Feedback")

    employee_calls = {}
    employee_responses = {}
    employee_ratings_sum = {}
    employee_ratings_count = {}

    total_calls = 0
    total_responses = 0

    for record in records:

        employee = record.get(
            "اسم الموظف", "غير محدد"
        )

        if str(employee).strip() == "":
            employee = "غير محدد"

        # نقصر التحليل على فريق المتابعة الحالي بس
        if employee not in FOLLOWUP_TEAM_MEMBERS:
            continue

        record_date = _parse_date_safe(
            record.get("التاريخ", "")
        )

        if start_date and (
            not record_date
            or record_date < start_date
        ):
            continue

        if end_date and (
            not record_date
            or record_date > end_date
        ):
            continue

        try:
            calls = int(
                record.get("عدد المكالمات", 0)
            )
        except (ValueError, TypeError):
            calls = 0

        try:
            responses = int(
                record.get("عدد الطلاب الذين ردوا", 0)
            )
        except (ValueError, TypeError):
            responses = 0

        try:
            rating = float(
                record.get("التقييم", "")
            )
        except (ValueError, TypeError):
            rating = None

        employee_calls[employee] = (
            employee_calls.get(employee, 0) + calls
        )

        employee_responses[employee] = (
            employee_responses.get(employee, 0) + responses
        )

        if rating is not None:

            employee_ratings_sum[employee] = (
                employee_ratings_sum.get(employee, 0) + rating
            )

            employee_ratings_count[employee] = (
                employee_ratings_count.get(employee, 0) + 1
            )

        total_calls += calls
        total_responses += responses

    employee_avg_rating = {}

    for employee in employee_calls:

        count = employee_ratings_count.get(employee, 0)

        if count > 0:

            employee_avg_rating[employee] = round(
                employee_ratings_sum[employee] / count,
                2
            )

        else:

            employee_avg_rating[employee] = 0

    return {
        "employee_calls": employee_calls,
        "employee_responses": employee_responses,
        "employee_avg_rating": employee_avg_rating,
        "total_calls": total_calls,
        "total_responses": total_responses
    }


def get_daily_reports(target_date):
    """
    يرجع تقارير كل الموظفين فى يوم واحد بس من شيت "Feedback"
    (اسم الموظف، القسم، عدد المكالمات، عدد الردود، التقييم،
    نص التقرير، وقت الإرسال، حالة الإرسال) — عشان تتعمل منها
    قراءة/ملخص يومي سريع.
    """

    records = _get_sheet_records("Feedback")

    daily_reports = []

    for record in records:

        record_date = _parse_date_safe(
            record.get("التاريخ", "")
        )

        if record_date != target_date:
            continue

        daily_reports.append({
            "اسم الموظف": record.get("اسم الموظف", ""),
            "القسم": record.get("القسم", ""),
            "عدد المكالمات": record.get("عدد المكالمات", ""),
            "عدد الطلاب الذين ردوا": record.get(
                "عدد الطلاب الذين ردوا", ""
            ),
            "التقييم": record.get("التقييم", ""),
            "التقرير": record.get("التقرير", ""),
            "وقت الإرسال": record.get("وقت الإرسال", ""),
            "حالة الإرسال": record.get("حالة الإرسال", "")
        })

    daily_reports.sort(
        key=lambda item: item["اسم الموظف"]
    )

    return daily_reports


def get_monthly_feedback_summary(reference_date):
    """
    يرجع لكل موظف (كل الأقسام: دعم فني/سوشيال/متابعة)، خلال
    الشهر اللي فيه "reference_date":
    - عدد مرات التقرير (عدد الصفوف فى الشهر ده)
    - توزيع "حالة الإرسال" (منها تقدر تعرف كام مرة "متأخر" مثلًا،
      حسب القيم الحقيقية الموجودة فى الشيت)

    ملحوظة: الدالة دي عامة لكل الموظفين، مش مقيدة على فريق
    المتابعة (سارة/ملك) — عكس get_followup_team_stats اللي
    مخصصة للمكالمات/الردود بس.

    اختار تاريخ واحد بس (أي يوم فى الشهر المطلوب) وهو بيحدد
    الشهر كامل تلقائي.
    """

    records = _get_sheet_records("Feedback")

    month_start = reference_date.replace(day=1)

    days_in_month = calendar.monthrange(
        reference_date.year, reference_date.month
    )[1]

    month_end = reference_date.replace(day=days_in_month)

    employee_reports_count = {}
    employee_status_counts = {}

    for record in records:

        employee = record.get(
            "اسم الموظف", "غير محدد"
        )

        if str(employee).strip() == "":
            employee = "غير محدد"

        record_date = _parse_date_safe(
            record.get("التاريخ", "")
        )

        if not record_date:
            continue

        if record_date < month_start or record_date > month_end:
            continue

        employee_reports_count[employee] = (
            employee_reports_count.get(employee, 0) + 1
        )

        status_value = str(
            record.get("حالة الإرسال", "")
        ).strip()

        if status_value == "":
            status_value = "غير محدد"

        employee_status_counts.setdefault(employee, {})

        employee_status_counts[employee][status_value] = (
            employee_status_counts[employee].get(status_value, 0) + 1
        )

    employee_late_count = {}

    for employee, status_counts in employee_status_counts.items():

        late_count = 0

        for status_value, count in status_counts.items():

            # بيتحسب "تأخير" لو القيمة فيها كلمة "متأخر" أو "تأخير"
            if "متأخر" in status_value or "تأخير" in status_value:
                late_count += count

        employee_late_count[employee] = late_count

    return {
        "month_start": month_start,
        "month_end": month_end,
        "employee_reports_count": employee_reports_count,
        "employee_status_counts": employee_status_counts,
        "employee_late_count": employee_late_count
    }


# ==================================
# ☕ تحليل البريك (شيفت الاستراحة)
# ==================================

def get_break_dashboard_stats():
    """
    يحسب لكل موظف من شيت "Breaks":
    - عدد مرات عمل شيفت البريك (كل الصفوف، افتراضي أو معدّل)
    - عدد مرات الميعاد الافتراضي (5-7)
    - عدد مرات التعديل عن الميعاد الافتراضي
    وترتيب الموظفين تنازليًا حسب إجمالي عدد مرات البريك.
    """

    records = _get_sheet_records("Breaks")

    total_breaks = {}
    default_breaks = {}
    changed_breaks = {}

    for record in records:

        employee = record.get(
            "اسم الموظف", "غير محدد"
        )

        if str(employee).strip() == "":
            employee = "غير محدد"

        total_breaks[employee] = (
            total_breaks.get(employee, 0) + 1
        )

        status_value = str(
            record.get("الحالة", "")
        ).strip()

        if status_value == "معدّل":

            changed_breaks[employee] = (
                changed_breaks.get(employee, 0) + 1
            )

        else:

            default_breaks[employee] = (
                default_breaks.get(employee, 0) + 1
            )

    employee_ranking = sorted(
        total_breaks.items(),
        key=lambda item: item[1],
        reverse=True
    )

    return {
        "total_breaks": total_breaks,
        "default_breaks": default_breaks,
        "changed_breaks": changed_breaks,
        "employee_ranking": employee_ranking
    }


def get_registration_trend(start_date=None, end_date=None):
    """
    يرجع عدد التسجيلات (كل صف/تسجيل، مجمّعة من الشيتين) لكل
    يوم، مرتبة بالتاريخ، مفلترة على الفترة لو محددة. مفيد لرسم
    نمو التسجيلات مع الوقت.
    """

    daily_counts = {}

    for sheet_name in ["Students 1", "Students 3"]:

        records = _get_sheet_records(sheet_name)

        for record in records:

            registration_date = _parse_date_safe(
                record.get("تاريخ التسجيل", "")
            )

            if not registration_date:
                continue

            if start_date and registration_date < start_date:
                continue

            if end_date and registration_date > end_date:
                continue

            daily_counts[registration_date] = (
                daily_counts.get(registration_date, 0) + 1
            )

    sorted_dates = sorted(daily_counts.keys())

    return [
        {"date": d, "count": daily_counts[d]}
        for d in sorted_dates
    ]


def get_students_data():

    return _get_sheet_records("Students")


def get_dashboard_stats():

    students = get_students_data()

    total_students = len(students)

    total_revenue = 0

    course_stats = {}
    employee_stats = {}
    employee_revenue = {}
    governorate_stats = {}

    for student in students:

        # =====================
        # Revenue
        # =====================

        try:
            revenue = int(
                student.get(
                    "سعر الاشتراك",
                    0
                )
            )
        except:
            revenue = 0

        total_revenue += revenue

        # =====================
        # Course
        # =====================

        course = student.get(
            "الكورس",
            "غير محدد"
        )

        course_stats[course] = (
            course_stats.get(
                course,
                0
            ) + 1
        )

        # =====================
        # Employee
        # =====================

        employee = student.get(
            "اسم الموظف",
            "غير محدد"
        )

        employee_stats[employee] = (
            employee_stats.get(
                employee,
                0
            ) + 1
        )

        employee_revenue[employee] = (
            employee_revenue.get(
                employee,
                0
            ) + revenue
        )

        # =====================
        # Governorate
        # =====================

        governorate = student.get(
            "المحافظة",
            "غير محدد"
        )

        governorate_stats[governorate] = (
            governorate_stats.get(
                governorate,
                0
            ) + 1
        )

    average_revenue = 0

    if total_students > 0:

        average_revenue = (
            total_revenue /
            total_students
        )

    employee_ranking = sorted(
        employee_revenue.items(),
        key=lambda x: x[1],
        reverse=True
    )

    return {

        "total_students":
            total_students,

        "total_revenue":
            total_revenue,

        "average_revenue":
            round(
                average_revenue,
                2
            ),

        "course_stats":
            course_stats,

        "employee_stats":
            employee_stats,

        "employee_revenue":
            employee_revenue,

        "employee_ranking":
            employee_ranking,

        "governorate_stats":
            governorate_stats
    }

def get_today_stats():
    """
    إحصائيات اليوم، محسوبة من شيتات "Students 1" و "Students 3"
    (بدل شيت "Students" القديم).
    """

    today = datetime.now().date()

    grade_1_today = _compute_today_stats_for_sheet(
        "Students 1", COURSES_GRADE_1, today
    )

    grade_3_today = _compute_today_stats_for_sheet(
        "Students 3", COURSES_GRADE_3, today
    )

    today_students = (
        grade_1_today["students_today"]
        + grade_3_today["students_today"]
    )

    today_revenue = (
        grade_1_today["revenue_today"]
        + grade_3_today["revenue_today"]
    )

    combined_employee_counts = {}

    for emp, cnt in grade_1_today["employee_counts"].items():
        combined_employee_counts[emp] = (
            combined_employee_counts.get(emp, 0) + cnt
        )

    for emp, cnt in grade_3_today["employee_counts"].items():
        combined_employee_counts[emp] = (
            combined_employee_counts.get(emp, 0) + cnt
        )

    # مفيش تعارض فى الأسامي بين كورسات أولى وتالتة، فالدمج مباشر
    combined_course_counts = {
        **grade_1_today["course_counts"],
        **grade_3_today["course_counts"]
    }

    best_employee_today = None

    if combined_employee_counts:
        best_employee_today = max(
            combined_employee_counts,
            key=combined_employee_counts.get
        )

    best_course_today = None

    if combined_course_counts:
        best_course_today = max(
            combined_course_counts,
            key=combined_course_counts.get
        )

    return {
        "today_students": today_students,
        "today_revenue": today_revenue,
        "best_employee_today": best_employee_today,
        "best_course_today": best_course_today
    }