import re
from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from ..models import Group, Member

PHONE_RE = re.compile(r"^0[789][01]\d{8}$")


class MemberFormError(ValueError):
    def __init__(self, errors: dict[str, str]):
        super().__init__("; ".join(errors.values()))
        self.errors = errors


@dataclass
class MemberInput:
    full_name: str
    phone: str
    trade: str


def normalize_phone(raw: str) -> str:
    """Accept 0803 123 4567, +234 803 123 4567, 234-803-123-4567; return 08031234567."""
    digits = re.sub(r"[^\d+]", "", raw or "")
    if digits.startswith("+234"):
        digits = "0" + digits[4:]
    elif digits.startswith("234") and len(digits) == 13:
        digits = "0" + digits[3:]
    return digits


def parse_form(form: dict[str, str]) -> MemberInput:
    errors: dict[str, str] = {}
    full_name = " ".join(form.get("full_name", "").split())
    if not full_name:
        errors["full_name"] = "Enter the member's name."
    phone = normalize_phone(form.get("phone", ""))
    if not PHONE_RE.match(phone):
        errors["phone"] = "Enter a Nigerian mobile number, e.g. 0803 123 4567."
    if errors:
        raise MemberFormError(errors)
    return MemberInput(full_name=full_name, phone=phone, trade=form.get("trade", "").strip())


def add_member(db: Session, group: Group, data: MemberInput) -> Member:
    next_position = max((m.payout_position for m in group.members), default=0) + 1
    member = Member(group=group, payout_position=next_position, **data.__dict__)
    db.add(member)
    db.commit()
    return member


def update_member(db: Session, member: Member, data: MemberInput) -> Member:
    for key, value in data.__dict__.items():
        setattr(member, key, value)
    db.commit()
    return member


def remove_member(db: Session, member: Member) -> None:
    """Remove a member who has made no payments; later members move up one place."""
    if member.payments:
        raise MemberFormError({"member": "This member has payments recorded and cannot be removed."})
    group_id, position = member.group_id, member.payout_position
    db.delete(member)
    db.flush()
    later = db.scalars(
        select(Member)
        .where(Member.group_id == group_id, Member.payout_position > position)
        .order_by(Member.payout_position)
    )
    for other in later:
        db.execute(
            update(Member).where(Member.id == other.id).values(payout_position=other.payout_position - 1)
        )
    db.commit()


def search(db: Session, query: str) -> list[Member]:
    query = query.strip()
    members = db.scalars(
        select(Member).options(selectinload(Member.group)).order_by(Member.full_name)
    ).all()
    if not query:
        return list(members)
    needle = query.lower()
    digits = normalize_phone(query)
    return [
        m
        for m in members
        if needle in m.full_name.lower()
        or needle in m.trade.lower()
        or (digits.isdigit() and digits in m.phone)
    ]
