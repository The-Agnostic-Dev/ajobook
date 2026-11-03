from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from ..dates import lagos_today
from ..models import Member, Payment, utcnow
from . import fees, schedule, summary

LEDGER_PAGE_SIZE = 10


class PaymentError(ValueError):
    pass


@dataclass(frozen=True)
class LedgerPage:
    payments: list[Payment]
    page: int
    pages: int
    total: int


def record_payment(
    db: Session,
    member: Member,
    *,
    cycle: int,
    amount_kobo: int,
    paid_on: date,
    note: str = "",
    form_token: str | None = None,
    recorded_at: datetime | None = None,
) -> Payment:
    group = member.group
    if schedule.get_cycle(group, cycle) is None:
        raise PaymentError(f"{group.name} has no month {cycle}.")
    if amount_kobo <= 0:
        raise PaymentError("The amount must be more than ₦0.")
    if paid_on > lagos_today():
        raise PaymentError("The payment date cannot be in the future.")

    payment = Payment(
        member=member,
        cycle=cycle,
        amount_kobo=amount_kobo,
        paid_on=paid_on,
        note=note.strip(),
        form_token=form_token or None,
        recorded_at=recorded_at or utcnow(),
    )
    payment.late_fee_kobo = fees.late_fee_for(group, payment)
    db.add(payment)
    db.commit()
    summary.invalidate(group.id)
    return payment


def find_by_token(db: Session, form_token: str) -> Payment | None:
    """The payment already saved from this copy of the form, if any."""
    return db.scalar(select(Payment).where(Payment.form_token == form_token))


def delete_payment(db: Session, payment: Payment) -> None:
    group_id = payment.member.group_id
    db.delete(payment)
    db.commit()
    summary.invalidate(group_id)


def recent_payments(db: Session, limit: int = 8) -> list[Payment]:
    return list(
        db.scalars(
            select(Payment)
            .options(joinedload(Payment.member).joinedload(Member.group))
            .order_by(Payment.recorded_at, Payment.id)
            .limit(limit)
        )
    )


def ledger(db: Session, group_id: int, page: int = 1) -> LedgerPage:
    total = db.scalar(
        select(func.count(Payment.id)).join(Member).where(Member.group_id == group_id)
    )
    pages = max(1, total // LEDGER_PAGE_SIZE)
    page = min(max(1, page), pages)
    rows = db.scalars(
        select(Payment)
        .join(Member)
        .options(joinedload(Payment.member))
        .where(Member.group_id == group_id)
        .order_by(Payment.paid_on.desc(), Payment.id.desc())
        .offset((page - 1) * LEDGER_PAGE_SIZE)
        .limit(LEDGER_PAGE_SIZE)
    )
    return LedgerPage(list(rows), page, pages, total)
