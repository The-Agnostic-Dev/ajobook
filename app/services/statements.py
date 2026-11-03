from collections import defaultdict
from dataclasses import dataclass
from datetime import date

from ..dates import lagos_today
from ..models import Group, Member, Payment
from . import schedule


@dataclass(frozen=True)
class StatementLine:
    cycle: schedule.Cycle
    expected_kobo: int
    paid_kobo: int
    late_fee_kobo: int
    is_due: bool

    @property
    def outstanding_kobo(self) -> int:
        return max(0, self.expected_kobo - self.paid_kobo) if self.is_due else 0

    @property
    def state(self) -> str:
        if self.paid_kobo >= self.expected_kobo:
            return "Paid"
        if self.paid_kobo > 0:
            return "Part paid"
        return "Owing" if self.is_due else "Not due"


@dataclass(frozen=True)
class Statement:
    member: Member
    lines: list[StatementLine]
    payments: list[Payment]
    payout_cycle: schedule.Cycle | None

    @property
    def total_paid_kobo(self) -> int:
        return sum(line.paid_kobo for line in self.lines)

    @property
    def total_late_fees_kobo(self) -> int:
        return sum(line.late_fee_kobo for line in self.lines)

    @property
    def arrears_kobo(self) -> int:
        return sum(line.outstanding_kobo for line in self.lines)


def _paid_by_cycle(payments: list[Payment]) -> tuple[dict[int, int], dict[int, int]]:
    paid: dict[int, int] = defaultdict(int)
    fees: dict[int, int] = defaultdict(int)
    for p in payments:
        paid[p.cycle] += p.amount_kobo
        fees[p.cycle] += p.late_fee_kobo
    return paid, fees


def member_statement(member: Member, today: date | None = None) -> Statement:
    today = today or lagos_today()
    group = member.group
    paid, fees = _paid_by_cycle(member.payments)
    lines = [
        StatementLine(
            cycle=c,
            expected_kobo=group.contribution_kobo,
            paid_kobo=paid[c.number],
            late_fee_kobo=fees[c.number],
            is_due=c.due_date <= today,
        )
        for c in schedule.cycles(group)
    ]
    payout = schedule.get_cycle(group, member.payout_position)
    payments = sorted(member.payments, key=lambda p: (p.paid_on, p.id), reverse=True)
    return Statement(member=member, lines=lines, payments=payments, payout_cycle=payout)


@dataclass(frozen=True)
class BalanceRow:
    member: Member
    paid_kobo: int
    arrears_kobo: int
    late_fees_kobo: int


def group_balances(group: Group, today: date | None = None) -> list[BalanceRow]:
    rows = []
    for member in group.members:
        st = member_statement(member, today)
        rows.append(BalanceRow(member, st.total_paid_kobo, st.arrears_kobo, st.total_late_fees_kobo))
    return rows


@dataclass(frozen=True)
class PayoutLine:
    member: Member
    paid_kobo: int
    late_fee_kobo: int
    expected_kobo: int

    @property
    def state(self) -> str:
        if self.paid_kobo >= self.expected_kobo:
            return "Paid"
        return "Part paid" if self.paid_kobo else "Not paid"


@dataclass(frozen=True)
class PayoutDay:
    group: Group
    cycle: schedule.Cycle
    lines: list[PayoutLine]

    @property
    def expected_kobo(self) -> int:
        return self.group.contribution_kobo * len(self.lines)

    @property
    def collected_kobo(self) -> int:
        return sum(line.paid_kobo for line in self.lines)

    @property
    def late_fees_kobo(self) -> int:
        return sum(line.late_fee_kobo for line in self.lines)

    @property
    def outstanding_kobo(self) -> int:
        return sum(max(0, line.expected_kobo - line.paid_kobo) for line in self.lines)

    @property
    def unpaid(self) -> list[PayoutLine]:
        return [line for line in self.lines if line.state != "Paid"]


def payout_day(group: Group, cycle: schedule.Cycle) -> PayoutDay:
    lines = []
    for member in group.members:
        in_cycle = [p for p in member.payments if p.cycle == cycle.number]
        lines.append(
            PayoutLine(
                member=member,
                paid_kobo=sum(p.amount_kobo for p in in_cycle),
                late_fee_kobo=sum(p.late_fee_kobo for p in in_cycle),
                expected_kobo=group.contribution_kobo,
            )
        )
    return PayoutDay(group, cycle, lines)
