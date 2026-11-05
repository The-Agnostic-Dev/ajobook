from datetime import date, datetime, timedelta, timezone

from app.models import Member
from app.services import payments, summary


def _last_month_start(today: date) -> date:
    first_this_month = today.replace(day=1)
    return (first_this_month - timedelta(days=1)).replace(day=1)


def test_collected_kobo_sums_all_cycle_one_payments_when_current_cycle_is_two(db, make_group):
    today = date.today()
    start = _last_month_start(today)
    group = make_group(members=6, start=start, due_day=15)
    members = (
        db.query(Member)
        .filter(Member.group_id == group.id)
        .order_by(Member.payout_position)
        .all()
    )

    paid_on = date(start.year, start.month, 15)
    amounts = [100_000, 150_000, 200_000, 250_000, 300_000, 350_000]
    recorded_at = datetime.now(timezone.utc).replace(tzinfo=None)

    for member, amount in zip(members, amounts):
        payments.record_payment(
            db,
            member,
            cycle=1,
            amount_kobo=amount,
            paid_on=paid_on,
            note="",
            recorded_at=recorded_at,
        )

    expected = sum(amounts)
    assert summary.group_summary(db, group).collected_kobo == expected


def test_collected_kobo_reflects_new_payment_immediately(db, make_group):
    today = date.today()
    start = _last_month_start(today)
    group = make_group(members=2, start=start, due_day=15)
    members = (
        db.query(Member)
        .filter(Member.group_id == group.id)
        .order_by(Member.payout_position)
        .all()
    )

    paid_on = date(start.year, start.month, 15)
    recorded_at = datetime.now(timezone.utc).replace(tzinfo=None)

    payments.record_payment(
        db,
        members[0],
        cycle=1,
        amount_kobo=100_000,
        paid_on=paid_on,
        note="",
        recorded_at=recorded_at,
    )
    assert summary.group_summary(db, group).collected_kobo == 100_000

    payments.record_payment(
        db,
        members[1],
        cycle=1,
        amount_kobo=150_000,
        paid_on=paid_on,
        note="",
        recorded_at=recorded_at,
    )
    assert summary.group_summary(db, group).collected_kobo == 250_000
