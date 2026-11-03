from dataclasses import dataclass
from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from ..models import LAST_DAY, Group, Member
from ..money import AmountError, naira_input, parse_naira

DUE_DAY_CHOICES: list[tuple[int, str]] = [(d, f"{d}") for d in range(1, 29)] + [
    (LAST_DAY, "Last day of the month")
]


class GroupFormError(ValueError):
    def __init__(self, errors: dict[str, str]):
        super().__init__("; ".join(errors.values()))
        self.errors = errors


@dataclass
class GroupInput:
    name: str
    contribution_kobo: int
    start_month: date
    due_day: int
    grace_days: int
    late_fee_kobo: int
    meeting_place: str


def list_groups(db: Session) -> list[Group]:
    return list(
        db.scalars(select(Group).options(selectinload(Group.members)).order_by(Group.name))
    )


def form_values(group: Group | None = None) -> dict[str, str]:
    """Initial values for the group form, as strings for the template."""
    if group is None:
        return {
            "name": "",
            "contribution": "",
            "start_month": "",
            "due_day": "5",
            "grace_days": "3",
            "late_fee": "0",
            "meeting_place": "",
        }
    return {
        "name": group.name,
        "contribution": naira_input(group.contribution_kobo),
        "start_month": group.start_month.strftime("%Y-%m"),
        "due_day": str(group.due_day),
        "grace_days": str(group.grace_days),
        "late_fee": naira_input(group.late_fee_kobo),
        "meeting_place": group.meeting_place,
    }


def parse_form(form: dict[str, str]) -> GroupInput:
    errors: dict[str, str] = {}
    name = form.get("name", "").strip()
    if not name:
        errors["name"] = "Give the group a name."

    contribution = 0
    try:
        contribution = parse_naira(form.get("contribution", ""))
        if contribution <= 0:
            errors["contribution"] = "The monthly contribution must be more than ₦0."
    except AmountError as exc:
        errors["contribution"] = str(exc)

    late_fee = 0
    try:
        late_fee = parse_naira(form.get("late_fee", "") or "0")
        if late_fee < 0:
            errors["late_fee"] = "The late fee cannot be negative."
    except AmountError as exc:
        errors["late_fee"] = str(exc)

    start_month = date.today().replace(day=1)
    try:
        year, month = (int(p) for p in form.get("start_month", "").split("-"))
        start_month = date(year, month, 1)
    except ValueError:
        errors["start_month"] = "Pick the month of the first contribution."

    valid_days = {d for d, _ in DUE_DAY_CHOICES}
    due_day = int(form.get("due_day") or 0) if (form.get("due_day") or "").isdigit() else 0
    if due_day not in valid_days:
        errors["due_day"] = "Pick a due day."

    grace_raw = (form.get("grace_days") or "0").strip()
    grace_days = int(grace_raw) if grace_raw.isdigit() else -1
    if not 0 <= grace_days <= 14:
        errors["grace_days"] = "Grace days must be between 0 and 14."

    if errors:
        raise GroupFormError(errors)
    return GroupInput(
        name=name,
        contribution_kobo=contribution,
        start_month=start_month,
        due_day=due_day,
        grace_days=grace_days,
        late_fee_kobo=late_fee,
        meeting_place=form.get("meeting_place", "").strip(),
    )


def create_group(db: Session, data: GroupInput) -> Group:
    group = Group(**data.__dict__)
    db.add(group)
    db.commit()
    return group


def update_group(db: Session, group: Group, data: GroupInput) -> Group:
    for key, value in data.__dict__.items():
        setattr(group, key, value)
    db.commit()
    return group


def member_count(group: Group) -> int:
    return len(group.members)


def recipients_in_order(group: Group) -> list[Member]:
    return sorted(group.members, key=lambda m: m.payout_position)
