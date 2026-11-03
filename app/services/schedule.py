"""Contribution calendar for a group.

Cycle 1 falls in the group's start month, cycle 2 in the month after, and so on.
There is one cycle per member: in cycle N everybody contributes and the member at
payout position N collects the pot.
"""

from dataclasses import dataclass
from datetime import date, timedelta

from ..dates import add_months, day_in_month, lagos_today
from ..models import Group, Member


@dataclass(frozen=True)
class Cycle:
    number: int
    due_date: date
    recipient: Member | None

    @property
    def month(self) -> date:
        return self.due_date.replace(day=1)


def cycle_count(group: Group) -> int:
    return len(group.members)


def due_dates(group: Group) -> list[date]:
    count = cycle_count(group)
    if count == 0:
        return []
    start = group.start_month
    dates = [day_in_month(start.year, start.month, group.due_day)]
    while len(dates) < count:
        dates.append(add_months(dates[-1], 1))
    return dates


def cycles(group: Group) -> list[Cycle]:
    by_position = {m.payout_position: m for m in group.members}
    return [Cycle(n, due, by_position.get(n)) for n, due in enumerate(due_dates(group), start=1)]


def get_cycle(group: Group, number: int) -> Cycle | None:
    for cycle in cycles(group):
        if cycle.number == number:
            return cycle
    return None


def late_after(group: Group, cycle: Cycle) -> date:
    """Last day a contribution for `cycle` can be paid without a late fee."""
    return cycle.due_date + timedelta(days=group.grace_days)


def current_cycle(group: Group, today: date | None = None) -> Cycle | None:
    """The cycle whose month is this month. None before the start or after the last payout."""
    today = today or lagos_today()
    this_month = today.replace(day=1)
    for cycle in cycles(group):
        if cycle.month == this_month:
            return cycle
    return None


def status(group: Group, today: date | None = None) -> str:
    today = today or lagos_today()
    all_cycles = cycles(group)
    if not all_cycles:
        return "No members yet"
    if today.replace(day=1) < all_cycles[0].month:
        return "Not started"
    if today.replace(day=1) > all_cycles[-1].month:
        return "Completed"
    return "Running"


def due_cycles(group: Group, today: date | None = None) -> list[Cycle]:
    """Cycles whose due date has arrived, i.e. contributions members should have made by now."""
    today = today or lagos_today()
    return [c for c in cycles(group) if c.due_date <= today]
