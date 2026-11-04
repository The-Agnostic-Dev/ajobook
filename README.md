# Ajobook

Ajobook is a record book for **ajo / esusu** coordinators: the person who runs a rotating savings
group, collects everybody's monthly contribution and hands the whole pot to one member each month.
It replaces the exercise book and the WhatsApp screenshots.

Coordinators use it to:

- set up a group (monthly contribution, first month, due day, grace days, late fee);
- add members in their **payout order** (position 1 collects in the first month, position 2 in the second, ...);
- record payments as they come in (cash, transfer, part payments);
- print a **member statement** for anyone who asks "how much have I paid?";
- open **Payout day** to see who has paid, who is owing and how much to hand over.

Everything is in Naira and in Lagos time.

## How the money works

| Rule | Detail |
| --- | --- |
| Cycles | One cycle (month) per member. A group of 10 runs for 10 months. |
| Pot | Monthly contribution x number of members. |
| Due date | The group's due day in each month. "Last day of the month" means the 30th, 31st or 28th/29th as the month has it (salary-day groups). |
| Grace days | A payment is on time if it is made on or before *due date + grace days*. Example: due on the 5th with 3 grace days, paying on the 8th is still on time. |
| Late fee | A flat fee charged once on each payment made after the grace period. It is worked out from the date the member **paid**, not the day the coordinator typed it in. |
| Group purse | Late fees go into the group purse. They are **not** part of anyone's payout. |
| Amount to hand over | On payout day: the contributions received for that month (late fees excluded). |
| Arrears | Contributions for months whose due date has arrived that are not fully paid. |
| Part payments | Allowed. A month shows "Part paid" until the full contribution is in. |
| Double submits | Each payment form carries a one-time token, so sending the same form twice records it once. |

New members join at the end of the rotation. Removing a member (only possible before they have paid
anything) moves everyone after them up one place.

## Running it

Requirements: Python 3.13.

```bash
python3.13 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/uvicorn app.main:app --reload --port 5111
```

Open http://localhost:5111.

With Docker:

```bash
docker compose up --build
```

On every start the demo data is reloaded (set `AJOBOOK_SEED_DEMO=0` to keep your data). The SQLite
file location is `AJOBOOK_DATABASE_URL`; see `.env.example`.

### Demo logins

| Username | Password | Who |
| --- | --- | --- |
| `ngozi` | `ajobook2026` | Ngozi Okafor, coordinator |
| `musa` | `ajobook2026` | Musa Bello, coordinator |

Both coordinators see all groups.

### Demo groups

Dates are relative to today, so the groups are always mid-cycle.

- **Balogun Market Traders Ajo**: 10 traders, ₦20,000 due on the 5th, 3 grace days, ₦1,000 late fee. Started 5 months ago.
- **Ministry of Works Staff Esusu**: 12 civil servants, ₦50,000 due on the last day of the month (salary day), no grace days, ₦2,500 late fee. Started 7 months ago.
- **Ikeja Food Sellers Ajo**: 6 food sellers, ₦10,000 due on the 15th, 2 grace days, ₦500 late fee. Started last month.

## Tests

```bash
.venv/bin/pytest
```

See [QA.md](QA.md) for the full QA workflow: setup, automated suite, and the manual checklist with expected results.

## Project layout

```
app/
  main.py            app factory, middleware, routers
  config.py          settings from environment variables
  db.py, models.py   SQLAlchemy 2 setup and tables (amounts stored in kobo)
  auth.py            coordinator login, flash messages
  money.py           Naira parsing and formatting
  dates.py           Lagos "today" and month arithmetic
  services/          business rules: schedule, fees, payments, statements, dashboard summary
  routes/            FastAPI routers (server-rendered pages)
  templates/         Jinja2 templates
  static/            CSS and a little JavaScript (confirm prompts, sortable tables)
  seed.py            demo data
tests/               pytest suite
```

