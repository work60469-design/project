# services/leave_service.py

from datetime import timedelta
from datetime import datetime

from services.sheets_service import get_sheet


EMERGENCY_YEARLY_LIMIT = 6
PLANNED_MONTHLY_LIMIT = 5
PLANNED_YEARLY_LIMIT = 15


def calculate_return_date(
    start_date,
    days
):
    return start_date + timedelta(days=days)


def save_leave(
    employee_name,
    leave_type,
    leave_days,
    start_date,
    return_date
):

    sheet = get_sheet("Leaves")

    sheet.append_row([
        employee_name,
        leave_type,
        leave_days,
        str(start_date),
        str(return_date),
        str(datetime.now())
    ])


def get_leaves_requested_today():
    """
    يرجع كل طلبات الإجازة اللي اتقدمت النهاردة بالتحديد
    (بناءً على عمود "تاريخ الطلب"، مش تاريخ بداية الإجازة).
    """

    leaves = get_all_leaves()

    today = datetime.now().strftime("%Y-%m-%d")

    today_requests = []

    for leave in leaves:

        request_timestamp = str(
            leave.get("تاريخ الطلب", "")
        ).strip()

        # عمود "تاريخ الطلب" فيه تاريخ ووقت كامل، فبنقارن
        # الجزء الأول (التاريخ) بس مع النهاردة
        request_date = request_timestamp.split(" ")[0]

        if request_date == today:
            today_requests.append(leave)

    return today_requests


def get_all_leaves():

    sheet = get_sheet("Leaves")

    return sheet.get_all_records()


def get_employee_leaves(
    employee_name
):

    leaves = get_all_leaves()

    return [
        leave
        for leave in leaves
        if leave["اسم الموظف"] == employee_name
    ]


def get_leave_statistics(
    employee_name
):

    leaves = get_employee_leaves(
        employee_name
    )

    today = datetime.today()

    current_month = today.month
    current_year = today.year

    emergency_used = 0

    planned_monthly_used = 0

    planned_yearly_used = 0

    for leave in leaves:

        try:

            start_date = datetime.strptime(
                leave["تاريخ البداية"],
                "%Y-%m-%d"
            )

            days = int(
                leave["عدد الأيام"]
            )

            leave_type = leave[
                "نوع الإجازة"
            ]

            # -------------------
            # طارئة (سنوية دلوقتي، مش شهرية)
            # -------------------

            if (
                leave_type == "طارئة"
                and
                start_date.year == current_year
            ):

                emergency_used += days

            # -------------------
            # مخططة
            # -------------------

            if leave_type == "مخططة":

                if (
                    start_date.month
                    == current_month
                    and
                    start_date.year
                    == current_year
                ):

                    planned_monthly_used += days

                if (
                    start_date.year
                    == current_year
                ):

                    planned_yearly_used += days

        except:

            continue

    return {
        "emergency_used":
            emergency_used,

        "emergency_remaining":
            max(
                0,
                EMERGENCY_YEARLY_LIMIT
                - emergency_used
            ),

        "planned_monthly_used":
            planned_monthly_used,

        "planned_monthly_remaining":
            max(
                0,
                PLANNED_MONTHLY_LIMIT
                - planned_monthly_used
            ),

        "planned_yearly_used":
            planned_yearly_used,

        "planned_yearly_remaining":
            max(
                0,
                PLANNED_YEARLY_LIMIT
                - planned_yearly_used
            )
    }

def get_available_planned_days(
    employee_name
):

    stats = get_leave_statistics(
        employee_name
    )

    monthly_remaining = stats[
        "planned_monthly_remaining"
    ]

    yearly_remaining = stats[
        "planned_yearly_remaining"
    ]

    remaining = min(
        monthly_remaining,
        yearly_remaining
    )

    return list(
        range(
            1,
            remaining + 1
        )
    )