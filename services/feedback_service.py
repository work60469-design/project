# services/feedback_service.py

from datetime import datetime
from datetime import timedelta

from services.sheets_service import get_sheet


# الديدلاين: 11 مساءً بتاريخ نفس اليوم
FEEDBACK_DEADLINE_HOUR = 23

# فترة السماح بالتعديل: لحد 11 الصبح من اليوم التالي
EDIT_GRACE_HOUR = 11


def get_feedback_sheet():

    return get_sheet(
        "Feedback"
    )


def _row_to_dict(row_values):
    """
    يحول صف خام (ليستة قيم بترتيبها فى الشيت) لصورة منظمة
    بأسماء واضحة، حسب نفس ترتيب الأعمدة المستخدم فى save_feedback.
    """

    def get_at(index, default=""):

        if index < len(row_values):
            return row_values[index]

        return default

    return {
        "employee_name": get_at(0),
        "department": get_at(1),
        "feedback_date": get_at(2),
        "activations": get_at(3),
        "calls_count": get_at(4),
        "answered_count": get_at(5),
        "rating": get_at(6),
        "report": get_at(7),
        "submission_time": get_at(8),
        "lateness_status": get_at(9)
    }


def get_last_feedback(employee_name):
    """
    يرجع آخر تسجيل فيدباك عمله الموظف ده (بغض النظر عن التاريخ)،
    مع رقم السطر الحقيقى فى الشيت. بيرجع None لو مفيش أي تسجيل.
    """

    sheet = get_feedback_sheet()

    all_values = sheet.get_all_values()

    last_result = None

    # بنتجاهل صف العناوين (أول صف فى الشيت)
    for index, row_values in enumerate(all_values[1:]):

        row = _row_to_dict(row_values)

        if row["employee_name"] == employee_name:

            last_result = {
                "row_number": index + 2,
                "data": row
            }

    return last_result


def is_feedback_editable(feedback_date_str):
    """
    بيحدد لو لسه ينفع نعدل على فيدباك بتاريخ معين:
    - لو التسجيل بتاريخ النهاردة: ينفع طول الوقت
    - لو التسجيل بتاريخ إمبارح: ينفع بس لحد EDIT_GRACE_HOUR الصبح
    - أي تاريخ أقدم من كده: مايتعدلش
    """

    try:

        feedback_date = datetime.strptime(
            feedback_date_str,
            "%Y-%m-%d"
        ).date()

    except (TypeError, ValueError):

        return False

    now = datetime.now()
    today = now.date()

    if feedback_date == today:
        return True

    yesterday = today - timedelta(days=1)

    if (
        feedback_date == yesterday
        and
        now.hour < EDIT_GRACE_HOUR
    ):
        return True

    return False


def get_today_feedback(employee_name):
    """
    يرجع تسجيل الفيدباك بتاع الموظف ده النهاردة (لو موجود)،
    مع رقم السطر الحقيقى فى الشيت (لاستخدامه فى التعديل).
    بيرجع None لو مفيش تسجيل النهاردة.
    """

    sheet = get_feedback_sheet()

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
            row["feedback_date"] == today
        ):

            return {
                "row_number": index + 2,
                "data": row
            }

    return None


def feedback_exists_today(
    employee_name
):

    return get_today_feedback(employee_name) is not None


def compute_lateness_status(
    feedback_date,
    submission_time
):
    """
    بيحدد لو التسجيل جه فى الميعاد أو متأخر، ولو متأخر بقد ايه.
    """

    deadline = datetime.strptime(
        feedback_date,
        "%Y-%m-%d"
    ).replace(
        hour=FEEDBACK_DEADLINE_HOUR,
        minute=0,
        second=0
    )

    if submission_time <= deadline:
        return "✅ فى الميعاد"

    delay = submission_time - deadline

    total_minutes = int(delay.total_seconds() // 60)

    hours = total_minutes // 60
    minutes = total_minutes % 60

    if hours > 0:
        return f"⏰ متأخر بـ {hours} ساعة و {minutes} دقيقة"

    return f"⏰ متأخر بـ {minutes} دقيقة"


def save_feedback(
    employee_name,
    department,
    feedback_date,
    activations,
    calls_count,
    answered_count,
    rating,
    report
):

    sheet = get_feedback_sheet()

    submission_time = datetime.now()

    lateness_status = compute_lateness_status(
        feedback_date,
        submission_time
    )

    sheet.append_row([

        employee_name,

        department,

        feedback_date,

        activations,

        calls_count,

        answered_count,

        rating,

        report,

        submission_time.strftime(
            "%Y-%m-%d %H:%M:%S"
        ),

        lateness_status

    ])


def update_feedback(
    row_number,
    employee_name,
    department,
    feedback_date,
    activations,
    calls_count,
    answered_count,
    rating,
    report,
    submission_time,
    lateness_status
):
    """
    يعدل على تسجيل فيدباك موجود فعلا (نفس السطر)، من غير ما يغير
    وقت الإرسال الأصلي أو حالة التأخير المحسوبة وقت أول تسجيل.
    """

    sheet = get_feedback_sheet()

    sheet.update(
        f"A{row_number}:J{row_number}",
        [[
            employee_name,
            department,
            feedback_date,
            activations,
            calls_count,
            answered_count,
            rating,
            report,
            submission_time,
            lateness_status
        ]]
    )