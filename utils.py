import jdatetime
from datetime import date

def date_to_jalali(gregorian_date: date) -> str:
    if not gregorian_date:
        return ""
    jalali_date = jdatetime.date.fromgregorian(date=gregorian_date)
    return jalali_date.strftime("%Y/%m/%d")

def jalali_to_date(year: int, month: int, day: int) -> date:
    return jdatetime.date(year, month, day).togregorian()