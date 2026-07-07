# services/feedback_dashboard_service.py

from services.sheets_service import get_sheet


def get_latest_feedback_per_employee():

    sheet = get_sheet(
        "Feedback"
    )

    rows = sheet.get_all_records()

    latest_feedback = {}

    for row in rows:

        employee = row.get(
            "اسم الموظف"
        )

        latest_feedback[
            employee
        ] = row

    return latest_feedback

def get_performance_stats():

    latest_feedback = (
        get_latest_feedback_per_employee()
    )

    support_stats = {}

    followup_stats = {}

    ratings = {}

    total_calls = 0

    total_answered = 0

    for employee, row in latest_feedback.items():

        department = row.get(
            "القسم",
            ""
        )

        try:

            rating = float(
                row.get(
                    "التقييم",
                    0
                )
            )

        except:

            rating = 0

        ratings[
            employee
        ] = rating

        # -----------------
        # Support
        # -----------------

        if department == "Support":

            try:

                activations = int(
                    row.get(
                        "عدد التفعيلات",
                        0
                    )
                )

            except:

                activations = 0

            support_stats[
                employee
            ] = activations

        # -----------------
        # Followup
        # -----------------

        elif department == "Followup":

            try:

                calls = int(
                    row.get(
                        "عدد المكالمات",
                        0
                    )
                )

            except:

                calls = 0

            try:

                answered = int(
                    row.get(
                        "عدد الطلاب الذين ردوا",
                        0
                    )
                )

            except:

                answered = 0

            not_answered = (
                calls - answered
            )

            followup_stats[
                employee
            ] = {

                "calls":
                    calls,

                "answered":
                    answered,

                "not_answered":
                    not_answered,

                "response_rate":
                    (
                        answered / calls * 100
                        if calls > 0
                        else 0
                    )
            }

            total_calls += calls

            total_answered += answered

    avg_rating = 0

    if ratings:

        avg_rating = (
            sum(
                ratings.values()
            )
            /
            len(
                ratings
            )
        )

    return {

        "support_stats":
            support_stats,

        "followup_stats":
            followup_stats,

        "ratings":
            ratings,

        "total_calls":
            total_calls,

        "total_answered":
            total_answered,

        "total_not_answered":
            (
                total_calls
                -
                total_answered
            ),

        "avg_rating":
            round(
                avg_rating,
                2
            )
    }