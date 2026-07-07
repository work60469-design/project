# services/leave_dashboard_service.py

from datetime import datetime

from services.sheets_service import get_sheet


def get_leave_dashboard_stats():

    sheet = get_sheet("Leaves")

    leaves = sheet.get_all_records()

    current_month = datetime.now().month
    current_year = datetime.now().year

    total_leaves = 0

    emergency_count = 0

    planned_count = 0

    employee_leaves = {}

    for leave in leaves:

        try:

            start_date = datetime.strptime(
                leave["تاريخ البداية"],
                "%Y-%m-%d"
            )

        except:

            continue

        if (
            start_date.month != current_month
            or
            start_date.year != current_year
        ):

            continue

        total_leaves += 1

        employee = leave.get(
            "اسم الموظف",
            "غير محدد"
        )

        employee_leaves[
            employee
        ] = (
            employee_leaves.get(
                employee,
                0
            ) + 1
        )

        leave_type = leave.get(
            "نوع الإجازة",
            ""
        )

        if leave_type == "طارئة":

            emergency_count += 1

        elif leave_type == "مخططة":

            planned_count += 1

    top_employee = None

    if employee_leaves:

        top_employee = max(
            employee_leaves,
            key=employee_leaves.get
        )

    return {

        "total_leaves":
            total_leaves,

        "emergency_count":
            emergency_count,

        "planned_count":
            planned_count,

        "top_employee":
            top_employee,

        "employee_leaves":
            employee_leaves
    }