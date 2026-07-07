# services/attendance_service.py

from datetime import datetime

from services.sheets_service import get_sheet


def get_attendance_sheet():

    return get_sheet(
        "Attendance"
    )


def attendance_exists_today(
    employee_name
):

    sheet = get_attendance_sheet()

    rows = sheet.get_all_records()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    for row in rows:

        if (
            row.get(
                "اسم الموظف"
            ) == employee_name
            and
            str(
                row.get(
                    "التاريخ"
                )
            ) == today
        ):

            return True

    return False


def has_checked_out_today(
    employee_name
):

    sheet = get_attendance_sheet()

    rows = sheet.get_all_records()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    for row in rows:

        if (
            row.get(
                "اسم الموظف"
            ) == employee_name
            and
            str(
                row.get(
                    "التاريخ"
                )
            ) == today
        ):

            if row.get(
                "وقت الانصراف"
            ):

                return True

    return False


def save_check_in(
    employee_name
):

    sheet = get_attendance_sheet()

    now = datetime.now()

    attendance_time = now.strftime(
        "%H:%M"
    )

    status = "في الموعد"

    if (
        now.hour > 11
        or
        (
            now.hour == 11
            and
            now.minute > 0
        )
    ):

        status = "متأخر"

    sheet.append_row([

        employee_name,

        now.strftime(
            "%Y-%m-%d"
        ),

        attendance_time,

        "",

        "",

        status
    ])


def save_check_out(
    employee_name
):

    sheet = get_attendance_sheet()

    rows = sheet.get_all_records()

    today = datetime.now().strftime(
        "%Y-%m-%d"
    )

    current_time = datetime.now()

    for index, row in enumerate(
        rows,
        start=2
    ):

        if (
            row.get(
                "اسم الموظف"
            ) == employee_name
            and
            str(
                row.get(
                    "التاريخ"
                )
            ) == today
        ):

            check_in_time = row.get(
                "وقت الحضور"
            )

            if not check_in_time:

                return False

            check_in_datetime = datetime.strptime(
                check_in_time,
                "%H:%M"
            )

            check_in_full = current_time.replace(
                hour=check_in_datetime.hour,
                minute=check_in_datetime.minute,
                second=0,
                microsecond=0
            )

            worked_hours = round(
                (
                    current_time
                    -
                    check_in_full
                ).total_seconds()
                /
                3600,
                2
            )

            # تحديث وقت الانصراف + ساعات العمل
            sheet.update(

                f"D{index}:E{index}",

                [[
                    current_time.strftime(
                        "%H:%M"
                    ),

                    worked_hours
                ]]
            )

            return True

    return False