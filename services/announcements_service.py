# services/announcements_service.py

from datetime import datetime

from services.sheets_service import get_sheet
from services.dashboard_service import _get_sheet_records


# اسم شيت الإعلانات فى الملف. لو سميته بشكل مختلف، غيّر القيمة
# دي بس وكل حاجة تانية هتفضل شغالة زي ما هي.
ANNOUNCEMENTS_SHEET_NAME = "الإعلانات"


def get_announcements():
    """
    يرجع كل الإعلانات، الأحدث الأول. كل إعلان بيترفق معاه
    "_row_number" (رقم الصف الحقيقي فى الشيت) عشان نقدر نمسحه
    بعدين لو حبينا.
    """

    records = _get_sheet_records(ANNOUNCEMENTS_SHEET_NAME)

    announcements = []

    for index, record in enumerate(records):

        item = dict(record)

        # +1 عشان الهيدر هو الصف الأول، +1 تانية عشان الفهرسة
        # فى جوجل شيتس بتبدأ من 1 مش من صفر
        item["_row_number"] = index + 2

        announcements.append(item)

    announcements.sort(
        key=lambda item: str(item.get("تاريخ الإعلان", "")),
        reverse=True
    )

    return announcements


def add_announcement(title, text, employee_name=""):
    """
    يضيف إعلان جديد كصف جديد فى شيت "الإعلانات". بيقرا هيدر
    الشيت الفعلي ويبني الصف حسب ترتيب الأعمدة الحقيقي.
    """

    sheet = get_sheet(ANNOUNCEMENTS_SHEET_NAME)

    headers = sheet.row_values(1)

    data = {
        "تاريخ الإعلان": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "العنوان": title,
        "النص": text,
        "اسم الناشر": employee_name
    }

    row = [str(data.get(header, "")) for header in headers]

    sheet.append_row(row, value_input_option="USER_ENTERED")

    # نفضي الكاش عشان الإعلان الجديد يظهر فورًا لكل حد
    _get_sheet_records.clear()


def delete_announcement(row_number):
    """
    يمسح إعلان معيّن نهائيًا برقم صفه الحقيقي فى الشيت (جاي من
    "_row_number" اللي بترجعه get_announcements).
    """

    sheet = get_sheet(ANNOUNCEMENTS_SHEET_NAME)

    sheet.delete_rows(row_number)

    _get_sheet_records.clear()