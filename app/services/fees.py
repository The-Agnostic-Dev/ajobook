from ..models import Group, Payment
from . import schedule


def late_fee_for(group: Group, payment: Payment) -> int:
    """Late fee (kobo) for a contribution, using the group's grace days."""
    if group.late_fee_kobo <= 0:
        return 0
    cycle = schedule.get_cycle(group, payment.cycle)
    if cycle is None:
        return 0
    paid_on = payment.paid_on
    if paid_on > schedule.late_after(group, cycle):
        return group.late_fee_kobo
    return 0
