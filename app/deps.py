from fastapi import Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .db import get_db
from .models import Group, Member, Payment


def group_or_404(group_id: int, db: Session = Depends(get_db)) -> Group:
    group = db.scalar(
        select(Group)
        .where(Group.id == group_id)
        .options(selectinload(Group.members).selectinload(Member.payments))
    )
    if group is None:
        raise HTTPException(404, "No such group")
    return group


def load_member(db: Session, member_id: int) -> Member:
    member = db.scalar(
        select(Member)
        .where(Member.id == member_id)
        .options(selectinload(Member.payments), selectinload(Member.group).selectinload(Group.members))
    )
    if member is None:
        raise HTTPException(404, "No such member")
    return member


def member_or_404(member_id: int, db: Session = Depends(get_db)) -> Member:
    return load_member(db, member_id)


def payment_or_404(payment_id: int, db: Session = Depends(get_db)) -> Payment:
    payment = db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(404, "No such payment")
    return payment
