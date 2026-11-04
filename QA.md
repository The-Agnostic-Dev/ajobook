# Ajobook QA Workflow

This document defines the QA workflow for Ajobook. The QA team follows these steps in order. Any deviation or failed step means the build fails QA.

## Prerequisites

- Python 3.13 installed.
- Internet access to install Python packages.

## Setup

1. Clone the repository and `cd` into it.
2. Create a virtual environment:
   ```bash
   python3.13 -m venv .venv
   ```
3. Install dependencies:
   ```bash
   .venv/bin/pip install -r requirements-dev.txt
   ```

## Automated Test Suite

Run the pytest suite:

```bash
.venv/bin/pytest
```

The command must exit with code 0. Any failing test fails QA.

## Manual Testing

Start the application on port 5111 with demo data:

```bash
.venv/bin/uvicorn app.main:app --reload --port 5111
```

Open http://localhost:5111 in a web browser. The demo data is reloaded on every start, so the state is deterministic.

Use the demo login `ngozi` / `ajobook2026` (coordinator Ngozi Okafor) for the manual checklist. `musa` / `ajobook2026` (Musa Bello) is an alternative login with the same access.

### Manual Checklist

Perform each step and verify the expected result.

1. **Log in**
   - Navigate to the login page.
   - Enter username `ngozi` and password `ajobook2026`.
   - Submit.
   - **Expected:** You are redirected to the dashboard. A welcome message appears, and the three demo groups are listed.

2. **Dashboard cards and recent payments**
   - On the dashboard, observe the group summary cards.
   - **Expected:** Three cards are shown:
     - *Balogun Market Traders Ajo*: 10 members, ₦20,000 monthly contribution.
     - *Ministry of Works Staff Esusu*: 12 members, ₦50,000 monthly contribution.
     - *Ikeja Food Sellers Ajo*: 6 members, ₦10,000 monthly contribution.
   - A "Recent payments" section is visible and lists the latest payments across all groups (may be empty if none have been recorded yet).

3. **Group detail, schedule, and payout day**
   - Click on *Balogun Market Traders Ajo*.
   - **Expected:** The group detail page shows:
     - Monthly contribution: ₦20,000.
     - Due day: 5.
     - Grace days: 3.
     - Late fee: ₦1,000.
     - Started 5 months ago (the exact month/year is relative to today).
   - Navigate to the group's schedule (payout order).
     - **Expected:** 10 members are listed in payout order, positions 1 through 10.
   - Navigate to *Payout day* for the current month.
     - **Expected:** A list of members with payment status (paid, part paid, owing) for the current cycle. The amount to hand over equals the sum of contributions received for that month (late fees excluded).

4. **Member search and statement**
   - Use the member search feature (search for any member name, e.g., the first member of the Balogun group).
   - **Expected:** The search results show the matching member.
   - Click on the member to view their statement.
   - **Expected:** The statement shows their payment history (if any), total amount paid, outstanding arrears (if any), and their position in the payout order.

5. **Recording payments**
   - For a member of the Balogun group who has not paid for the current month, record an **on-time payment** of ₦20,000 with today's date.
     - **Expected:** The payment is saved. The member's status for the current month becomes "Paid". No late fee is added.
   - Record a **late-fee payment** for a previous month (choose a date more than 3 days after that month's due date, e.g., the 10th of that month). Enter ₦20,000.
     - **Expected:** The payment is saved and flagged as late. A late fee of ₦1,000 is added to the group purse (visible on the group's purse summary). The late fee is not part of the member's contribution or the payout amount.
   - Record a **part payment** of ₦5,000 for a member for the current month.
     - **Expected:** The payment is saved. The member's status for that month shows "Part paid" and the remaining amount is displayed.
   - Attempt to **duplicate** the previous part payment by submitting the same form again (using the same one-time token, e.g., by pressing back and resubmitting).
     - **Expected:** Only one payment is recorded. The duplicate submission is ignored.

6. **Removing a payment**
   - Choose a recorded payment (e.g., the on-time payment from step 5) and delete it.
   - **Expected:** The payment is removed. The member's status reverts to "Owing" or "Part paid" as appropriate. Totals on the dashboard and group pages update accordingly.

7. **Adding, editing, and removing a member**
   - In the Balogun group, add a new member with a name and no prior payments.
     - **Expected:** The member is added at the end of the payout order (position 11).
   - Edit the new member's name.
     - **Expected:** The name is updated everywhere.
   - Remove the new member (they have not paid anything).
     - **Expected:** The member is removed, and the payout order returns to 10 members. Members after the removed one shift up one position.
   - Attempt to remove a member who has already made a payment.
     - **Expected:** The removal is rejected with an error message, and the member remains.

8. **Group form validation**
   - Navigate to create a new group.
   - Enter invalid data: negative monthly contribution, due day 32, negative grace days, or empty group name.
   - Submit the form.
   - **Expected:** The form displays validation errors for each invalid field. No group is created.

## Pass/Fail Criteria

- **Pass:** The automated test suite exits with code 0, and every manual checklist step produces the expected result.
- **Fail:** Any automated test fails, or any manual step does not match its expected result. The build fails QA and must be fixed.
