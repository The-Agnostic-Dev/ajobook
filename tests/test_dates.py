from datetime import date

from app.dates import add_months, day_in_month, long_date, shift_month


def test_shift_month_across_years():
    assert shift_month(date(2026, 11, 1), 3) == date(2027, 2, 1)
    assert shift_month(date(2026, 1, 1), -1) == date(2025, 12, 1)


def test_day_in_month_clamps():
    assert day_in_month(2026, 2, 31) == date(2026, 2, 28)
    assert day_in_month(2028, 2, 31) == date(2028, 2, 29)
    assert day_in_month(2026, 7, 5) == date(2026, 7, 5)


def test_add_months_clamps_to_month_end():
    assert add_months(date(2026, 1, 31), 1) == date(2026, 2, 28)
    assert add_months(date(2026, 3, 15), 2) == date(2026, 5, 15)


def test_long_date():
    assert long_date(date(2026, 3, 7)) == "7 Mar 2026"
