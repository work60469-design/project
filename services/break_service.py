# services/break_service.py

from datetime import datetime

from services.sheets_service import get_sheet


DEFAULT_BREAK_START_HOUR = 17  # 5 مساءً
DEFAULT_BREAK_DURATION_HOURS = 2

STATUS_DEFAULT = "الميعاد الافتراضي (5-7)"
STATUS_CHANGED = "معدّل"


def get_break_sheet():

    return get_sheet(
        "Breaks"
    )


def _row_to_dict(row_values):

    def get_at(index, default=""):

        if index < len(row_values):
            return row_values[index]

        return default

    return {
        "employee_name": get_at(0),
        "break_date": get_at(1),
        "start_time": get_at(2),
        "end_time": get_at(3),
        "status": get_at(4)
    }


def is_default_time(start_time_str):
    """
    بيحدد لو ميعاد البداية المدخل هو الميعاد الافتراضي (5 مساءً)
    أم لا.
    """

    try:

        start_time = datetime.strptime(
            start_time_str,
            "%H:%M"
        ).time()

    except (ValueError, TypeError):

        return False

    return (
        start_time.hour == DEFAULT_BREAK_START_HOUR
        and
        start_time.minute == 0
    )


def get_today_break(employee_name):
    """
    يرجع بريك الموظف ده النهاردة (لو موجود)، مع رقم السطر
    الحقيقى فى الشيت (لاستخدامه فى التعديل). بيرجع None لو
    مفيش تسجيل النهاردة.
    """

    sheet = get_break_sheet()

    all_values = sheet.get_all_values()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    # بنتجاهل صف العناوين (أول صف فى الشيت)
    for index, row_values in enumerate(all_values[1:]):

        row = _row_to_dict(row_values)

        if (
            row["employee_name"] == employee_name
            and
            row["break_date"] == today
        ):

            return {
                "row_number": index + 2,
                "data": row
            }

    return None


def save_break(
    employee_name,
    break_date,
    start_time,
    end_time
):

    sheet = get_break_sheet()

    status = (
        STATUS_DEFAULT
        if is_default_time(start_time)
        else STATUS_CHANGED
    )

    sheet.append_row([
        employee_name,
        break_date,
        start_time,
        end_time,
        status
    ])


def update_break(
    row_number,
    employee_name,
    break_date,
    start_time,
    end_time
):

    sheet = get_break_sheet()

    status = (
        STATUS_DEFAULT
        if is_default_time(start_time)
        else STATUS_CHANGED
    )

    sheet.update(
        f"A{row_number}:E{row_number}",
        [[
            employee_name,
            break_date,
            start_time,
            end_time,
            status
        ]]
    )


def get_today_break_changes():
    """
    يرجع كل البريكات اللي اتغيّرت عن الميعاد الافتراضي
    والمسجلة النهاردة بالتحديد (مفيد للإشعارات فى الصفحة
    الرئيسية للأدمن).
    """

    sheet = get_break_sheet()

    all_values = sheet.get_all_values()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    changes = []

    for row_values in all_values[1:]:

        row = _row_to_dict(row_values)

        if (
            row["break_date"] == today
            and
            row["status"] == STATUS_CHANGED
        ):

            changes.append(row)

    return changes