from datetime import date

from app.services import schedule


def test_one_cycle_per_member(make_group):
    group = make_group(members=4, start=date(2026, 1, 1), due_day=5)
    dates = schedule.due_dates(group)
    assert dates == [date(2026, 1, 5), date(2026, 2, 5), date(2026, 3, 5), date(2026, 4, 5)]


def test_recipient_follows_payout_position(make_group):
    group = make_group(members=3)
    assert [c.recipient.full_name for c in schedule.cycles(group)] == ["Member 1", "Member 2", "Member 3"]


def test_current_cycle_and_status(make_group):
    group = make_group(members=4, start=date(2026, 1, 1), due_day=5)
    assert schedule.current_cycle(group, date(2026, 3, 1)).number == 3
    assert schedule.current_cycle(group, date(2025, 12, 20)) is None
    assert schedule.status(group, date(2025, 12, 20)) == "Not started"
    assert schedule.status(group, date(2026, 2, 10)) == "Running"
    assert schedule.status(group, date(2026, 5, 1)) == "Completed"


def test_late_after_adds_grace_days(make_group):
    group = make_group(members=2, start=date(2026, 1, 1), due_day=5, grace_days=3)
    assert schedule.late_after(group, schedule.get_cycle(group, 1)) == date(2026, 1, 8)


def test_due_cycles(make_group):
    group = make_group(members=4, start=date(2026, 1, 1), due_day=5)
    assert [c.number for c in schedule.due_cycles(group, date(2026, 2, 5))] == [1, 2]
