import calendar
from datetime import date, datetime

from .config import LAGOS


def lagos_today() -> date:
    return datetime.now(LAGOS).date()


def shift_month(month_start: date, months: int) -> date:
    """First day of the month `months` after `month_start`."""
    index = month_start.year * 12 + (month_start.month - 1) + months
    return date(index // 12, index % 12 + 1, 1)


def day_in_month(year: int, month: int, day: int) -> date:
    """The given day of a month, or the month's last day if the month is shorter."""
    last = calendar.monthrange(year, month)[1]
    return date(year, month, min(day, last))


def add_months(d: date, months: int) -> date:
    first = shift_month(d.replace(day=1), months)
    return day_in_month(first.year, first.month, d.day)


def month_label(d: date) -> str:
    return d.strftime("%B %Y")


def long_date(d: date | None) -> str:
    return d.strftime("%-d %b %Y") if d else ""
