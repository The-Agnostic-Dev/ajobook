from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import current_coordinator, flash
from ..db import get_db
from ..deps import group_or_404
from ..models import Group
from ..services import groups as group_service
from ..services import members as member_service
from ..services import payments as payment_service
from ..services import schedule, statements
from ..templating import render

router = APIRouter(prefix="/groups", dependencies=[Depends(current_coordinator)])


def _form_page(request: Request, group: Group | None, form: dict, errors: dict | None = None):
    return render(
        request,
        "groups/form.html",
        {
            "group": group,
            "form": form,
            "errors": errors or {},
            "due_days": group_service.DUE_DAY_CHOICES,
        },
        status_code=400 if errors else 200,
    )


@router.get("/new")
def new_group(request: Request):
    return _form_page(request, None, group_service.form_values())


@router.post("/new")
async def create_group(request: Request, db: Session = Depends(get_db)):
    form = {k: str(v) for k, v in (await request.form()).items()}
    try:
        data = group_service.parse_form(form)
    except group_service.GroupFormError as exc:
        return _form_page(request, None, form, exc.errors)
    group = group_service.create_group(db, data)
    flash(request, f"{group.name} created. Now add the members in their payout order.")
    return RedirectResponse(f"/groups/{group.id}", status_code=303)


@router.get("/{group_id}")
def group_detail(request: Request, group: Group = Depends(group_or_404)):
    cycles = {c.number: c for c in schedule.cycles(group)}
    return render(
        request,
        "groups/detail.html",
        {
            "group": group,
            "rotation": [(m, cycles.get(m.payout_position)) for m in group_service.recipients_in_order(group)],
            "current": schedule.current_cycle(group),
            "status": schedule.status(group),
            "balances": statements.group_balances(group),
            "member_form": {"full_name": "", "phone": "", "trade": ""},
            "member_errors": {},
        },
    )


@router.get("/{group_id}/edit")
def edit_group(request: Request, group: Group = Depends(group_or_404)):
    return _form_page(request, group, group_service.form_values(group))


@router.post("/{group_id}/edit")
async def update_group(request: Request, group: Group = Depends(group_or_404), db: Session = Depends(get_db)):
    form = {k: str(v) for k, v in (await request.form()).items()}
    try:
        data = group_service.parse_form(form)
    except group_service.GroupFormError as exc:
        return _form_page(request, group, form, exc.errors)
    group_service.update_group(db, group, data)
    flash(request, "Group settings saved.")
    return RedirectResponse(f"/groups/{group.id}", status_code=303)


@router.get("/{group_id}/schedule")
def group_schedule(request: Request, group: Group = Depends(group_or_404)):
    current = schedule.current_cycle(group)
    return render(
        request,
        "groups/schedule.html",
        {"group": group, "cycles": schedule.cycles(group), "current": current},
    )


@router.get("/{group_id}/payments")
def group_payments(request: Request, page: int = 1, group: Group = Depends(group_or_404), db: Session = Depends(get_db)):
    return render(
        request,
        "groups/payments.html",
        {"group": group, "ledger": payment_service.ledger(db, group.id, page)},
    )


@router.get("/{group_id}/payout")
def payout(request: Request, cycle: int | None = None, group: Group = Depends(group_or_404)):
    chosen = schedule.get_cycle(group, cycle) if cycle else schedule.current_cycle(group)
    all_cycles = schedule.cycles(group)
    if chosen is None:
        if not all_cycles:
            raise HTTPException(404, "This group has no members yet")
        chosen = all_cycles[-1] if schedule.status(group) == "Completed" else all_cycles[0]
    return render(
        request,
        "groups/payout.html",
        {"group": group, "day": statements.payout_day(group, chosen), "cycles": all_cycles},
    )


@router.post("/{group_id}/members")
async def add_member(request: Request, group: Group = Depends(group_or_404), db: Session = Depends(get_db)):
    form = {k: str(v) for k, v in (await request.form()).items()}
    try:
        data = member_service.parse_form(form)
    except member_service.MemberFormError as exc:
        flash(request, "Member not added: " + str(exc), "error")
        return RedirectResponse(f"/groups/{group.id}#add-member", status_code=303)
    member = member_service.add_member(db, group, data)
    flash(request, f"{member.full_name} added at position {member.payout_position}.")
    return RedirectResponse(f"/groups/{group.id}", status_code=303)
