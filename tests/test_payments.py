from datetime import date, datetime, timedelta

import pytest

from app.dates import lagos_today
from app.services import payments, statements


def _at(day: date) -> datetime:
    return datetime(day.year, day.month, day.day, 16, 0)


def test_payment_inside_grace_has_no_late_fee(db, make_group):
    group = make_group(start=date(2026, 1, 1), due_day=5, grace_days=3)
    member = group.members[0]
    p = payments.record_payment(
        db, member, cycle=1, amount_kobo=1_000_000, paid_on=date(2026, 1, 8), recorded_at=_at(date(2026, 1, 8))
    )
    assert p.late_fee_kobo == 0


def test_payment_after_grace_is_charged(db, make_group):
    group = make_group(start=date(2026, 1, 1), due_day=5, grace_days=3, late_fee_kobo=50_000)
    member = group.members[0]
    p = payments.record_payment(
        db, member, cycle=1, amount_kobo=1_000_000, paid_on=date(2026, 1, 9), recorded_at=_at(date(2026, 1, 9))
    )
    assert p.late_fee_kobo == 50_000


@pytest.mark.parametrize("amount", [0, -100])
def test_amount_must_be_positive(db, make_group, amount):
    group = make_group()
    with pytest.raises(payments.PaymentError):
        payments.record_payment(db, group.members[0], cycle=1, amount_kobo=amount, paid_on=date(2026, 1, 5))


def test_future_dates_rejected(db, make_group):
    group = make_group()
    with pytest.raises(payments.PaymentError):
        payments.record_payment(
            db, group.members[0], cycle=1, amount_kobo=100, paid_on=lagos_today() + timedelta(days=1)
        )


def test_unknown_month_rejected(db, make_group):
    group = make_group(members=3)
    with pytest.raises(payments.PaymentError):
        payments.record_payment(db, group.members[0], cycle=4, amount_kobo=100, paid_on=date(2026, 1, 5))


def test_statement_totals(db, make_group):
    group = make_group(members=3, start=date(2026, 1, 1), contribution_kobo=1_000_000)
    member = group.members[1]
    for cycle, amount in ((1, 1_000_000), (2, 400_000)):
        payments.record_payment(
            db, member, cycle=cycle, amount_kobo=amount, paid_on=date(2026, cycle, 4), recorded_at=_at(date(2026, cycle, 4))
        )
    db.refresh(member)
    st = statements.member_statement(member, today=date(2026, 3, 20))
    assert st.total_paid_kobo == 1_400_000
    assert st.arrears_kobo == 600_000 + 1_000_000
    assert [line.state for line in st.lines] == ["Paid", "Part paid", "Owing"]
    assert st.payout_cycle.number == 2


def test_payout_day_excludes_late_fees_from_handover(db, make_group):
    group = make_group(members=2, start=date(2026, 1, 1), contribution_kobo=1_000_000, late_fee_kobo=50_000)
    a, b = group.members
    payments.record_payment(db, a, cycle=1, amount_kobo=1_000_000, paid_on=date(2026, 1, 4), recorded_at=_at(date(2026, 1, 4)))
    payments.record_payment(db, b, cycle=1, amount_kobo=1_000_000, paid_on=date(2026, 1, 20), recorded_at=_at(date(2026, 1, 20)))
    db.refresh(a)
    db.refresh(b)
    day = statements.payout_day(group, group and statements.schedule.get_cycle(group, 1))
    assert day.collected_kobo == 2_000_000
    assert day.late_fees_kobo == 50_000
    assert day.outstanding_kobo == 0
    assert day.unpaid == []


def test_delete_payment(db, make_group):
    group = make_group()
    member = group.members[0]
    p = payments.record_payment(db, member, cycle=1, amount_kobo=500, paid_on=date(2026, 1, 5))
    payments.delete_payment(db, p)
    db.refresh(member)
    assert member.payments == []
