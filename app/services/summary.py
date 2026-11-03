"""Per-group figures for the dashboard cards.

Working these out touches every member and payment of a group, and the dashboard
shows all groups at once, so results are kept for a few minutes.
"""

import time
from dataclasses import dataclass

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models import Group, Member, Payment
from . import schedule

TTL_SECONDS = 600

_cache: dict[int, tuple[float, "GroupSummary"]] = {}


@dataclass(frozen=True)
class GroupSummary:
    group_id: int
    name: str
    member_count: int
    contribution_kobo: int
    pot_kobo: int
    status: str
    cycle_number: int | None
    cycle_total: int
    collector: str | None
    collected_kobo: int


def _build(db: Session, group: Group) -> GroupSummary:
    cycle = schedule.current_cycle(group)
    collected = 0
    if cycle is not None:
        collected = db.scalar(
            select(func.coalesce(func.sum(Payment.amount_kobo), 0))
            .join(Member)
            .where(Member.group_id == group.id, Payment.cycle == cycle.number)
        )
    return GroupSummary(
        group_id=group.id,
        name=group.name,
        member_count=len(group.members),
        contribution_kobo=group.contribution_kobo,
        pot_kobo=group.pot_kobo,
        status=schedule.status(group),
        cycle_number=cycle.number if cycle else None,
        cycle_total=schedule.cycle_count(group),
        collector=cycle.recipient.full_name if cycle and cycle.recipient else None,
        collected_kobo=collected,
    )


def group_summary(db: Session, group: Group) -> GroupSummary:
    hit = _cache.get(group.id)
    if hit and time.monotonic() - hit[0] < TTL_SECONDS:
        return hit[1]
    summary = _build(db, group)
    _cache[group.id] = (time.monotonic(), summary)
    return summary


def invalidate(group_id: int) -> None:
    _cache.pop(group_id, None)


def clear() -> None:
    _cache.clear()
