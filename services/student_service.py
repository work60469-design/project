# services/student_service.py

from services.sheets_service import get_sheet
from datetime import datetime


def normalize_phone(phone):

    phone = str(phone).strip()

    # لو Google Sheets شال الصفر الأول
    if phone.isdigit() and len(phone) == 10:
        phone = "0" + phone

    return phone



def get_all_students():

    students_1 = get_sheet("Students 1")
    students_3 = get_sheet("Students 3")

    return (
        students_1.get_all_records()
        +
        students_3.get_all_records()
    )



def student_exists(student_phone, grade):

    student_phone = normalize_phone(
        student_phone
    )


    # نبحث داخل شيت الصف فقط

    if grade == "أولى ثانوي":

        sheet = get_sheet(
            "Students 1"
        )

    else:

        sheet = get_sheet(
            "Students 3"
        )


    students = sheet.get_all_records()


    for student in students:

        existing_phone = normalize_phone(
            student.get(
                "رقم الطالب",
                ""
            )
        )


        if existing_phone == student_phone:

            return True


    return False



def get_headers_for_grade(grade):

    if grade == "أولى ثانوي":

        return [
            "اسم الطالب",
            "رقم الطالب",
            "المحافظة",
            "الحالة",
            "الرقم اللى محول منه",
            "الصف",
            "الترم الاول",
            "شهر 8",
            "شهر 9",
            "شهر 10",
            "شهر 11",
            "شهر 12",
            "شهر 1",
            "الملاحظة",
            "سبب الملاحظة",
            "تاريخ التسجيل",
            "اسم الموظف"
        ]

    else:

        return [
            "اسم الطالب",
            "رقم الطالب",
            "المحافظة",
            "الحالة",
            "الرقم اللى محول منه",
            "الصف",
            "السنوى",
            "الدعامة والحركة",
            "التنسيق الهرمونى",
            "التكاثر",
            "المناعة",
            "DNA & RNA",
            "الملاحظة",
            "سبب الملاحظة",
            "تاريخ التسجيل",
            "اسم الموظف"
        ]



def get_sheet_name_for_grade(grade):

    if grade == "أولى ثانوي":
        return "Students 1"

    return "Students 3"



def save_student(
    student_name,
    student_phone,
    governorate,
    student_status,
    transfer_phone,
    grade,
    note,
    note_reason,
    registration_date,
    employee_name,
    **courses
):


    # تحديد الشيت

    sheet_name = get_sheet_name_for_grade(grade)
    sheet = get_sheet(sheet_name)
    headers = get_headers_for_grade(grade)


    row = []


    for header in headers:


        if header == "اسم الطالب":
            row.append(student_name)


        elif header == "رقم الطالب":
            row.append(student_phone)


        elif header == "المحافظة":
            row.append(governorate)


        elif header == "الحالة":
            row.append(student_status)

        
        elif header == "الرقم اللى محول منه":
            row.append(transfer_phone)


        elif header == "الصف":
            row.append(grade)


        elif header in courses:
            row.append(courses[header])


        elif header == "الملاحظة":
            row.append(note)


        elif header == "سبب الملاحظة":
            row.append(note_reason)


        elif header == "تاريخ التسجيل":
            row.append(registration_date)


        elif header == "اسم الموظف":
            row.append(employee_name)


        else:
            row.append("")



    sheet.append_row(row)



def find_students_by_phone(student_phone):
    """
    يبحث فى الشيتين ("Students 1" و "Students 3") عن كل التسجيلات
    اللى ليها نفس رقم الموبايل (ممكن يرجع أكتر من نتيجة لنفس الطالب
    لو اتسجل أكتر من مرة).

    بيرجع ليستة, كل عنصر فيها dict فيه:
        - sheet_name: اسم الشيت اللى موجود فيه السطر
        - row_number: رقم السطر الحقيقى فى الشيت (لاستخدامه فى التعديل)
        - data: بيانات السطر نفسه
    """

    student_phone = normalize_phone(student_phone)

    results = []

    for sheet_name in ["Students 1", "Students 3"]:

        sheet = get_sheet(sheet_name)
        records = sheet.get_all_records()

        for index, record in enumerate(records):

            existing_phone = normalize_phone(
                record.get("رقم الطالب", "")
            )

            if existing_phone == student_phone:

                results.append({
                    "sheet_name": sheet_name,
                    # +2 = +1 لصف العناوين, +1 لأن الفهرسة بتبدأ من صفر
                    "row_number": index + 2,
                    "data": record
                })

    return results



def log_edit(
    employee_name,
    student_name,
    student_phone,
    grade,
    sheet_name,
    row_number,
    changes_text
):
    """
    يسجل فى شيت "Edit Log" تفاصيل أي تعديل بيحصل على بيانات طالب:
    امتى حصل، مين اللي عدل، وايه اللي اتغير بالظبط.
    """

    log_sheet = get_sheet("Edit Log")

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    log_sheet.append_row([
        timestamp,
        employee_name,
        student_name,
        student_phone,
        grade,
        sheet_name,
        row_number,
        changes_text
    ])



def delete_student(sheet_name, row_number):
    """
    يحذف سطر بالكامل من الشيت (حذف تسجيل طالب نهائيًا).
    """

    sheet = get_sheet(sheet_name)
    sheet.delete_rows(row_number)



def update_student(
    sheet_name,
    row_number,
    student_name,
    student_phone,
    governorate,
    student_status,
    transfer_phone,
    grade,
    note,
    note_reason,
    registration_date,
    employee_name,
    **courses
):
    """
    يحدث سطر موجود فعلا فى الشيت (تعديل مباشر على نفس السطر
    بدل إضافة سطر جديد).
    """

    sheet = get_sheet(sheet_name)
    headers = get_headers_for_grade(grade)

    row = []

    for header in headers:

        if header == "اسم الطالب":
            row.append(student_name)

        elif header == "رقم الطالب":
            row.append(student_phone)

        elif header == "المحافظة":
            row.append(governorate)

        elif header == "الحالة":
            row.append(student_status)

        elif header == "الرقم اللى محول منه":
            row.append(transfer_phone)

        elif header == "الصف":
            row.append(grade)

        elif header in courses:
            row.append(courses[header])

        elif header == "الملاحظة":
            row.append(note)

        elif header == "سبب الملاحظة":
            row.append(note_reason)

        elif header == "تاريخ التسجيل":
            row.append(registration_date)

        elif header == "اسم الموظف":
            row.append(employee_name)

        else:
            row.append("")

    last_column_letter = chr(64 + len(headers))
    cell_range = f"A{row_number}:{last_column_letter}{row_number}"

    sheet.update(cell_range, [row])