import secrets

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import current_coordinator, flash
from ..db import get_db
from ..deps import member_or_404
from ..models import Member
from ..services import members as member_service
from ..services import schedule, statements
from ..templating import render

router = APIRouter(prefix="/members", dependencies=[Depends(current_coordinator)])


@router.get("")
def search_members(request: Request, q: str = "", db: Session = Depends(get_db)):
    return render(request, "members/search.html", {"q": q, "results": member_service.search(db, q)})


def statement_context(member: Member, payment_form: dict | None = None, errors: str | None = None) -> dict:
    group = member.group
    current = schedule.current_cycle(group)
    default_cycle = current.number if current else 1
    return {
        "member": member,
        "group": group,
        "statement": statements.member_statement(member),
        "cycles": schedule.cycles(group),
        "payment_form": payment_form
        or {"cycle": str(default_cycle), "amount": "", "paid_on": "", "note": ""},
        "payment_error": errors,
        "form_token": secrets.token_urlsafe(16),
    }


@router.get("/{member_id}")
def statement(request: Request, member: Member = Depends(member_or_404)):
    return render(request, "members/statement.html", statement_context(member))


@router.get("/{member_id}/edit")
def edit_member(request: Request, member: Member = Depends(member_or_404)):
    form = {"full_name": member.full_name, "phone": member.phone, "trade": member.trade}
    return render(request, "members/edit.html", {"member": member, "form": form, "errors": {}})


@router.post("/{member_id}/edit")
async def update_member(request: Request, member: Member = Depends(member_or_404), db: Session = Depends(get_db)):
    form = {k: str(v) for k, v in (await request.form()).items()}
    try:
        data = member_service.parse_form(form)
    except member_service.MemberFormError as exc:
        return render(
            request, "members/edit.html", {"member": member, "form": form, "errors": exc.errors}, status_code=400
        )
    member_service.update_member(db, member, data)
    flash(request, "Member details saved.")
    return RedirectResponse(f"/members/{member.id}", status_code=303)


@router.post("/{member_id}/remove")
def remove_member(request: Request, member: Member = Depends(member_or_404), db: Session = Depends(get_db)):
    group_id, name = member.group_id, member.full_name
    try:
        member_service.remove_member(db, member)
    except member_service.MemberFormError as exc:
        flash(request, str(exc), "error")
        return RedirectResponse(f"/members/{member.id}/edit", status_code=303)
    flash(request, f"{name} removed from the group.")
    return RedirectResponse(f"/groups/{group_id}", status_code=303)
