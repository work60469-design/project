# services/data_review_service.py

import pandas as pd

from services.sheets_service import get_sheet


PLATFORM_NAME_COLUMN = "اسم الطالب"
PLATFORM_PHONE_COLUMN = "رقم هاتف الطالب"
PLATFORM_EMPLOYEE_COLUMN = "المسئول عن الاشتراك"
PLATFORM_DATE_COLUMN = "تاريخ الاشتراك"

SHEET_NAME_COLUMN = "اسم الطالب"
SHEET_PHONE_COLUMN = "رقم الطالب"
SHEET_EMPLOYEE_COLUMN = "اسم الموظف"
SHEET_DATE_COLUMN = "تاريخ التسجيل"

SHEETS_TO_CHECK = ["Students 1", "Students 3"]


def normalize_phone(phone):

    digits = "".join(
        ch for ch in str(phone) if ch.isdigit()
    )

    if len(digits) == 10:
        digits = "0" + digits

    return digits


def normalize_name(name):

    return str(name).strip()


def normalize_employee(name):

    name = str(name).strip()

    # على المنصة اسم الموظف بييجي زي "رنا دعم"، وعندنا فى
    # الشيت بييجي "رنا". فبنشيل كلمة "دعم" عشان نقدر نقارن
    name = name.replace("دعم", "").strip()

    return name


def load_platform_records(csv_file):
    """
    بيقرا ملف الـ CSV اللي نزلته سارة من المنصة بالكامل، من غير
    أي فلترة بتاريخ (تاريخ الاشتراك فى ملف المنصة مالوش لازمة
    فى المقارنة؛ الفلترة بالتاريخ بتتم على الجوجل شيت بس، عشان
    منجيبش بيانات السنة كلها من الشيت).
    """

    dataframe = pd.read_csv(csv_file, encoding="utf-8-sig")

    records = []

    for _, row in dataframe.iterrows():

        raw_name = row.get(PLATFORM_NAME_COLUMN, "")
        raw_phone = row.get(PLATFORM_PHONE_COLUMN, "")
        raw_employee = row.get(PLATFORM_EMPLOYEE_COLUMN, "")

        records.append({
            "name": normalize_name(raw_name),
            "phone": normalize_phone(raw_phone),
            "employee": normalize_employee(raw_employee),
            "raw_name": raw_name,
            "raw_phone": raw_phone,
            "raw_employee": raw_employee
        })

    return records


def load_sheet_records(selected_date):
    """
    بيرجع تسجيلات الجوجل شيت (Students 1 + Students 3) اللي
    حصلت فى التاريخ المطلوب بس.
    """

    target_date = str(selected_date)

    records = []

    for sheet_name in SHEETS_TO_CHECK:

        sheet = get_sheet(sheet_name)

        rows = sheet.get_all_records()

        for row in rows:

            registration_date = str(
                row.get(SHEET_DATE_COLUMN, "")
            ).strip()

            if registration_date != target_date:
                continue

            raw_name = row.get(SHEET_NAME_COLUMN, "")
            raw_phone = row.get(SHEET_PHONE_COLUMN, "")
            raw_employee = row.get(SHEET_EMPLOYEE_COLUMN, "")

            records.append({
                "name": normalize_name(raw_name),
                "phone": normalize_phone(raw_phone),
                "employee": normalize_employee(raw_employee),
                "raw_name": raw_name,
                "raw_phone": raw_phone,
                "raw_employee": raw_employee
            })

    return records


def compare_records(platform_records, sheet_records):
    """
    بيقارن بين تسجيلات المنصة وتسجيلات الجوجل شيت باستخدام
    (الاسم + رقم الهاتف + اسم الموظف) بعد التطبيع. بيرجع:
    - missing_in_sheet: موجود فى المنصة وغير موجود فى الشيت
    - missing_in_platform: موجود فى الشيت وغير موجود فى المنصة
    """

    def make_key(record):
        return (
            record["name"],
            record["phone"],
            record["employee"]
        )

    sheet_keys = [make_key(r) for r in sheet_records]
    platform_keys = [make_key(r) for r in platform_records]

    missing_in_sheet = [
        record for record in platform_records
        if make_key(record) not in sheet_keys
    ]

    missing_in_platform = [
        record for record in sheet_records
        if make_key(record) not in platform_keys
    ]

    return missing_in_sheet, missing_in_platform