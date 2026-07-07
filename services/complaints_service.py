# services/complaints_service.py

from datetime import datetime

from services.sheets_service import get_sheet
from services.dashboard_service import (
    _get_sheet_records,
    _normalize_phone,
    COURSES_GRADE_1,
    COURSES_GRADE_3
)


# اسم شيت الشكاوى فى الملف. لو سميته بشكل مختلف، غيّر القيمة
# دي بس وكل حاجة تانية هتفضل شغالة زي ما هي.
COMPLAINTS_SHEET_NAME = "الشكاوى"


def search_student_by_phone(phone):
    """
    يدور على رقم الموبايل فى شيتات "Students 1" و "Students 3"
    ويرجع كل الصفوف المطابقة (ممكن الطالب يكون مسجل أكتر من
    مرة، أو فى الشيتين مع بعض).
    """

    normalized_phone = _normalize_phone(phone)

    if not normalized_phone:
        return []

    results = []

    sheets_to_search = [
        ("Students 1", "أولى ثانوي", COURSES_GRADE_1),
        ("Students 3", "3 ثانوي", COURSES_GRADE_3)
    ]

    for sheet_name, grade_label, courses in sheets_to_search:

        records = _get_sheet_records(sheet_name)

        for record in records:

            record_phone = _normalize_phone(
                record.get("رقم الطالب", "")
            )

            if record_phone != normalized_phone:
                continue

            enrolled_courses = [
                course for course in courses
                if str(record.get(course, "")).strip() != ""
            ]

            results.append({
                "الصف": grade_label,
                "اسم الطالب": record.get("اسم الطالب", ""),
                "رقم الطالب": record.get("رقم الطالب", ""),
                "المحافظة": record.get("المحافظة", ""),
                "الحالة": record.get("الحالة", ""),
                "الملاحظة": record.get("الملاحظة", ""),
                "سبب الملاحظة": record.get("سبب الملاحظة", ""),
                "الكورسات المشترك فيها": (
                    "، ".join(enrolled_courses)
                    if enrolled_courses else "-"
                ),
                "تاريخ التسجيل": record.get("تاريخ التسجيل", ""),
                "اسم الموظف": record.get("اسم الموظف", "")
            })

    return results


def get_complaints_by_phone(phone):
    """
    يرجع كل الشكاوى المسجّلة قبل كده لنفس رقم الموبايل من شيت
    "الشكاوى"، الأحدث الأول. كل شكوى بيترفق معاها "_row_number"
    (رقم الصف الحقيقي فى الشيت) عشان نقدر نعدّلها بعدين.
    """

    normalized_phone = _normalize_phone(phone)

    if not normalized_phone:
        return []

    records = _get_sheet_records(COMPLAINTS_SHEET_NAME)

    matching = []

    for index, record in enumerate(records):

        record_phone = _normalize_phone(
            record.get("رقم الموبايل", "")
        )

        if record_phone != normalized_phone:
            continue

        record_with_row = dict(record)

        # +1 عشان الهيدر هو الصف الأول، +1 تانية عشان الفهرسة
        # فى جوجل شيتس بتبدأ من 1 مش من صفر
        record_with_row["_row_number"] = index + 2

        matching.append(record_with_row)

    matching.sort(
        key=lambda item: str(item.get("تاريخ الشكوى", "")),
        reverse=True
    )

    return matching


def get_all_complaints():
    """
    يرجع كل الشكاوى المسجّلة على الإطلاق (لو حبيت تعمل بحث عام
    أو ليستة كاملة لاحقًا).
    """

    return _get_sheet_records(COMPLAINTS_SHEET_NAME)


def add_complaint(
    phone,
    student_name,
    grade_label,
    complaint_text,
    employee_name="",
    banned=False
):
    """
    يضيف شكوى جديدة كصف جديد فى شيت "الشكاوى". بيقرا هيدر
    الشيت الفعلي أول حاجة ويبني الصف حسب ترتيب الأعمدة الحقيقي،
    عشان لو الأعمدة اتغير ترتيبها فى الشيت يفضل شغال صح من غير
    ما نكسر حاجة.
    """

    sheet = get_sheet(COMPLAINTS_SHEET_NAME)

    headers = sheet.row_values(1)

    data = {
        "تاريخ الشكوى": datetime.now().strftime("%Y-%m-%d"),
        "رقم الموبايل": phone,
        "اسم الطالب": student_name,
        "الصف": grade_label,
        "نص الشكوى": complaint_text,
        "تم الحظر": "نعم" if banned else "لا",
        "اسم الموظف": employee_name
    }

    row = [str(data.get(header, "")) for header in headers]

    sheet.append_row(row, value_input_option="USER_ENTERED")

    # نفضي الكاش عشان الشكوى الجديدة تظهر فورًا فى أي بحث بعد كده
    _get_sheet_records.clear()


def update_complaint(
    row_number,
    student_name,
    grade_label,
    complaint_text,
    banned=False
):
    """
    يعدّل شكوى موجودة بالفعل (باستخدام رقم الصف الحقيقي بتاعها
    فى الشيت، جاي من "_row_number" اللي بترجعه
    get_complaints_by_phone). التاريخ الأصلي ورقم الموبايل
    واسم الموظف اللي سجّل الشكوى الأول مايتغيروش.
    """

    sheet = get_sheet(COMPLAINTS_SHEET_NAME)

    headers = sheet.row_values(1)

    data = {
        "اسم الطالب": student_name,
        "الصف": grade_label,
        "نص الشكوى": complaint_text,
        "تم الحظر": "نعم" if banned else "لا"
    }

    for header, value in data.items():

        if header in headers:

            column_index = headers.index(header) + 1

            sheet.update_cell(row_number, column_index, value)

    # نفضي الكاش عشان التعديل يظهر فورًا فى أي بحث بعد كده
    _get_sheet_records.clear()