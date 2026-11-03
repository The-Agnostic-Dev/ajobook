from datetime import UTC, date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


def utcnow() -> datetime:
    """Naive UTC timestamp (SQLite has no time zones)."""
    return datetime.now(UTC).replace(tzinfo=None)


# A due_day of 31 means "last day of the month" (30th, 28th/29th in February, ...).
LAST_DAY = 31


class Coordinator(Base):
    __tablename__ = "coordinators"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(40), unique=True)
    full_name: Mapped[str] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(200))


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    contribution_kobo: Mapped[int] = mapped_column(Integer)
    start_month: Mapped[date] = mapped_column(Date)  # always the 1st of the month
    due_day: Mapped[int] = mapped_column(Integer, default=5)
    grace_days: Mapped[int] = mapped_column(Integer, default=3)
    late_fee_kobo: Mapped[int] = mapped_column(Integer, default=0)
    meeting_place: Mapped[str] = mapped_column(String(160), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    members: Mapped[list["Member"]] = relationship(
        back_populates="group", order_by="Member.payout_position", cascade="all, delete-orphan"
    )

    @property
    def pot_kobo(self) -> int:
        return self.contribution_kobo * len(self.members)


class Member(Base):
    __tablename__ = "members"
    __table_args__ = (UniqueConstraint("group_id", "payout_position"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    full_name: Mapped[str] = mapped_column(String(120))
    phone: Mapped[str] = mapped_column(String(20))
    payout_position: Mapped[int] = mapped_column(Integer)
    trade: Mapped[str] = mapped_column(String(80), default="")
    joined_on: Mapped[date] = mapped_column(Date, default=date.today)

    group: Mapped[Group] = relationship(back_populates="members")
    payments: Mapped[list["Payment"]] = relationship(
        back_populates="member", order_by="Payment.paid_on", cascade="all, delete-orphan"
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[int] = mapped_column(primary_key=True)
    member_id: Mapped[int] = mapped_column(ForeignKey("members.id"))
    cycle: Mapped[int] = mapped_column(Integer)
    amount_kobo: Mapped[int] = mapped_column(Integer)
    late_fee_kobo: Mapped[int] = mapped_column(Integer, default=0)
    paid_on: Mapped[date] = mapped_column(Date)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    note: Mapped[str] = mapped_column(String(200), default="")
    form_token: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    member: Mapped[Member] = relationship(back_populates="payments")
