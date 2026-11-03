"""Demo data: three groups with dates relative to today, so the app always looks "live"."""

from datetime import date, datetime, time, timedelta, timezone

from sqlalchemy.orm import Session

from .auth import hash_password
from .config import LAGOS
from .dates import day_in_month, lagos_today, shift_month
from .models import LAST_DAY, Coordinator, Group, Member
from .services import payments

N = 100  # kobo per naira

BALOGUN = [
    ("Adunni Bakare", "08031234501", "Ankara fabric"),
    ("Chioma Eze", "08052233412", "Provisions"),
    ("Funmilayo Ogunleye", "07069981203", "Shoes and bags"),
    ("Ibrahim Danjuma", "08127745510", "Phone accessories"),
    ("Kemi Alabi", "09050012277", "Lace and George"),
    ("Kunle Adeyemi", "08164430921", "Electronics"),
    ("Ngozi Nwankwo", "08033318842", "Beads"),
    ("Rukayat Lawal", "07031127756", "Ready-made clothes"),
    ("Tolu Fashola", "08097781123", "Cosmetics"),
    ("Uche Obi", "08185501946", "Children's wear"),
]

MINISTRY = [
    ("Mrs. Bisi Akinola", "08023345671", "Admin officer"),
    ("Mr. Emeka Okonkwo", "08034456782", "Quantity surveyor"),
    ("Mrs. Halima Yusuf", "08065567893", "Accountant"),
    ("Mr. Segun Oladipo", "07036678904", "Driver"),
    ("Engr. Femi Adebayo", "08127789015", "Civil engineer"),
    ("Mrs. Grace Etim", "09018890126", "Typist"),
    ("Mr. Yemi Coker", "08159901237", "Procurement"),
    ("Mrs. Ifeoma Nnadi", "08060012348", "Store officer"),
    ("Mr. Tunde Bello", "07053323459", "Messenger"),
    ("Miss Amaka Ude", "08184434560", "Clerk"),
    ("Mr. Sola Ajayi", "08025545671", "Architect"),
    ("Mrs. Patience Okon", "09036656782", "Secretary"),
]

FOOD = [
    ("Iya Basira", "08037712093", "Amala spot"),
    ("Mama Nkechi", "08061198374", "Rice and beans"),
    ("Blessing Udo", "07065521449", "Small chops"),
    ("Aisha Garba", "08138807215", "Suya"),
    ("Mr. Jide Ogun", "09072213368", "Pepper soup"),
    ("Esther Okoro", "08143329907", "Puff-puff"),
]


def _recorded(day: date) -> datetime:
    """Payments in the demo were entered the evening they were paid."""
    local = datetime.combine(day, time(17, 30), tzinfo=LAGOS)
    return min(local.astimezone(timezone.utc), datetime.now(timezone.utc) - timedelta(hours=1)).replace(tzinfo=None)


def _members(db: Session, group: Group, people: list[tuple[str, str, str]], joined: date) -> list[Member]:
    out = []
    for position, (name, phone, trade) in enumerate(people, start=1):
        member = Member(group=group, full_name=name, phone=phone, trade=trade, payout_position=position, joined_on=joined)
        db.add(member)
        out.append(member)
    db.commit()
    return out


def _pay(db: Session, member: Member, cycle: int, naira: int, paid_on: date, note: str = "") -> None:
    payments.record_payment(
        db, member, cycle=cycle, amount_kobo=naira * N, paid_on=paid_on, note=note, recorded_at=_recorded(paid_on)
    )


def _balogun(db: Session, today: date) -> None:
    this_month = today.replace(day=1)
    start = shift_month(this_month, -5)
    group = Group(
        name="Balogun Market Traders Ajo",
        contribution_kobo=20_000 * N,
        start_month=start,
        due_day=5,
        grace_days=3,
        late_fee_kobo=1_000 * N,
        meeting_place="Shop 14B, Balogun Market, Lagos Island",
    )
    db.add(group)
    db.commit()
    people = _members(db, group, BALOGUN, start - timedelta(days=10))

    def due(cycle: int) -> date:
        m = shift_month(start, cycle - 1)
        return date(m.year, m.month, 5)

    adunni, chioma, funmi, ibrahim, kemi, kunle, ngozi, rukayat, tolu, uche = people
    for cycle in range(1, 6):
        for m in (adunni, chioma, ibrahim, ngozi, uche):
            if m is ibrahim and cycle == 3:
                _pay(db, m, cycle, 15_000, due(cycle) - timedelta(days=1), "Balance of 5k to come")
                continue
            _pay(db, m, cycle, 20_000, due(cycle) - timedelta(days=1), "Cash at the shop")
        _pay(db, rukayat, cycle, 20_000, due(cycle) + timedelta(days=2), "Transfer")
    # Tolu always pays late.
    for cycle in (1, 2, 3, 4, 5):
        _pay(db, tolu, cycle, 20_000, due(cycle) + timedelta(days=6), "Paid at the meeting")
    # Funmilayo is a month behind.
    for cycle in (1, 2, 3, 4):
        _pay(db, funmi, cycle, 20_000, due(cycle), "OPay transfer")
    # Kemi part-paid month 4 and has not caught up.
    for cycle in (1, 2, 3):
        _pay(db, kemi, cycle, 20_000, due(cycle) - timedelta(days=2))
    _pay(db, kemi, 4, 5_000, due(4) + timedelta(days=1), "Part payment, balance next week")
    # Kunle travelled after month 1.
    _pay(db, kunle, 1, 20_000, due(1), "Cash")
    # A few early birds for this month.
    early = min(today, due(6) - timedelta(days=1))
    for m in (adunni, chioma, ngozi):
        _pay(db, m, 6, 20_000, early, "Paid early")


def _ministry(db: Session, today: date) -> None:
    this_month = today.replace(day=1)
    start = shift_month(this_month, -7)
    group = Group(
        name="Ministry of Works Staff Esusu",
        contribution_kobo=50_000 * N,
        start_month=start,
        due_day=LAST_DAY,
        grace_days=0,
        late_fee_kobo=2_500 * N,
        meeting_place="Block 5, Alausa Secretariat, Ikeja",
    )
    db.add(group)
    db.commit()
    people = _members(db, group, MINISTRY, start - timedelta(days=20))

    def salary_day(cycle: int) -> date:
        m = shift_month(start, cycle - 1)
        return day_in_month(m.year, m.month, 31)

    for cycle in range(1, 8):
        for i, m in enumerate(people):
            if i == 9 and cycle >= 5:
                continue  # Amaka has been on leave without pay
            _pay(db, m, cycle, 50_000, salary_day(cycle), "Salary deduction")


def _food(db: Session, today: date) -> None:
    this_month = today.replace(day=1)
    start = shift_month(this_month, -1)
    group = Group(
        name="Ikeja Food Sellers Ajo",
        contribution_kobo=10_000 * N,
        start_month=start,
        due_day=15,
        grace_days=2,
        late_fee_kobo=500 * N,
        meeting_place="Computer Village gate, Ikeja",
    )
    db.add(group)
    db.commit()
    people = _members(db, group, FOOD, start - timedelta(days=5))
    first_due = date(start.year, start.month, 15)
    for m in people[:5]:
        _pay(db, m, 1, 10_000, first_due - timedelta(days=1), "Cash")
    _pay(db, people[5], 1, 10_000, first_due + timedelta(days=4), "Cash")


def seed_demo(db: Session, today: date | None = None) -> None:
    today = today or lagos_today()
    db.add_all(
        [
            Coordinator(username="ngozi", full_name="Ngozi Okafor", password_hash=hash_password("ajobook2026")),
            Coordinator(username="musa", full_name="Musa Bello", password_hash=hash_password("ajobook2026")),
        ]
    )
    db.commit()
    _balogun(db, today)
    _ministry(db, today)
    _food(db, today)
