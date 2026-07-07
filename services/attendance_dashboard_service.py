
# services/attendance_dashboard_service.py

from datetime import datetime

from auth.users import USERS

from services.sheets_service import (
    get_sheet
)


def get_attendance_stats():

    attendance_sheet = get_sheet(
        "Attendance"
    )

    leave_sheet = get_sheet(
        "Leaves"
    )

    attendance_rows = (
        attendance_sheet.get_all_records()
    )

    leave_rows = (
        leave_sheet.get_all_records()
    )

    current_month = (
        datetime.now().month
    )

    current_year = (
        datetime.now().year
    )

    working_days = (
        datetime.now().day
    )

    employees = []

    for username, user_data in USERS.items():

        if username == "amal":

            continue

        employees.append(
            user_data[
                "display_name"
            ]
        )

    attendance_stats = {}

    late_stats = {}

    absence_stats = {}

    leave_days_stats = {}

    hours_stats = {}

    for employee in employees:

        attendance_stats[
            employee
        ] = 0

        late_stats[
            employee
        ] = 0

        absence_stats[
            employee
        ] = 0

        leave_days_stats[
            employee
        ] = 0

        hours_stats[
            employee
        ] = []

    # ==================================
    # Attendance
    # ==================================

    for row in attendance_rows:

        employee = row.get(
            "اسم الموظف"
        )

        if employee not in employees:

            continue

        attendance_stats[
            employee
        ] += 1

        if row.get(
            "الحالة"
        ) == "متأخر":

            late_stats[
                employee
            ] += 1

        try:

            hours = float(

                row.get(
                    "عدد ساعات العمل",
                    0
                )
            )

            if hours > 0:

                hours_stats[
                    employee
                ].append(
                    hours
                )

        except:

            pass

    # ==================================
    # Leave Days
    # ==================================

    for leave in leave_rows:

        employee = leave.get(
            "اسم الموظف"
        )

        if employee not in employees:

            continue

        try:

            start_date = datetime.strptime(

                leave[
                    "تاريخ البداية"
                ],

                "%Y-%m-%d"
            )

        except:

            continue

        if (
            start_date.month
            != current_month
            or
            start_date.year
            != current_year
        ):

            continue

        try:

            leave_days = int(

                leave.get(
                    "عدد الأيام",
                    0
                )
            )

        except:

            leave_days = 0

        leave_days_stats[
            employee
        ] += leave_days

    # ==================================
    # Absence
    # ==================================

    for employee in employees:

        absence = (

            working_days

            -

            attendance_stats[
                employee
            ]

            -

            leave_days_stats[
                employee
            ]
        )

        if absence < 0:

            absence = 0

        absence_stats[
            employee
        ] = absence

    # ==================================
    # Average Hours
    # ==================================

    average_hours = {}

    for employee in employees:

        employee_hours = (
            hours_stats[
                employee
            ]
        )

        if employee_hours:

            average_hours[
                employee
            ] = round(

                sum(
                    employee_hours
                )
                /
                len(
                    employee_hours
                ),

                2
            )

        else:

            average_hours[
                employee
            ] = 0

    # ==================================
    # Best Employee
    # ==================================

    commitment_score = {}

    for employee in employees:

        commitment_score[
            employee
        ] = (

            attendance_stats[
                employee
            ]

            -

            absence_stats[
                employee
            ]

            -

            late_stats[
                employee
            ]
        )

    best_employee = max(

        commitment_score,

        key=commitment_score.get
    )

    worst_employee = min(

        commitment_score,

        key=commitment_score.get
    )

    return {

        "attendance":
            attendance_stats,

        "absence":
            absence_stats,

        "late":
            late_stats,

        "leave_days":
            leave_days_stats,

        "average_hours":
            average_hours,

        "best_employee":
            best_employee,

        "worst_employee":
            worst_employee
    }

