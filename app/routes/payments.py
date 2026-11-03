from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from ..auth import current_coordinator, flash
from ..db import get_db
from ..deps import load_member, payment_or_404
from ..models import Payment
from ..money import AmountError, format_naira, parse_naira
from ..services import payments as payment_service
from ..templating import render
from .members import statement_context

router = APIRouter(dependencies=[Depends(current_coordinator)])


@router.post("/members/{member_id}/payments")
def record_payment(
    request: Request,
    member_id: int,
    cycle: str = Form(""),
    amount: str = Form(""),
    paid_on: str = Form(""),
    note: str = Form(""),
    form_token: str = Form(""),
    db: Session = Depends(get_db),
):
    if form_token and payment_service.find_by_token(db, form_token):
        # Same form sent again (double click, or refresh after saving): keep the first one.
        flash(request, "That payment was already recorded.")
        return RedirectResponse(f"/members/{member_id}", status_code=303)
    member = load_member(db, member_id)
    form = {"cycle": cycle, "amount": amount, "paid_on": paid_on, "note": note}
    try:
        payment = payment_service.record_payment(
            db,
            member,
            cycle=int(cycle),
            amount_kobo=parse_naira(amount),
            paid_on=date.fromisoformat(paid_on),
            note=note,
            form_token=form_token or None,
        )
    except (AmountError, payment_service.PaymentError) as exc:
        return render(request, "members/statement.html", statement_context(member, form, str(exc)), status_code=400)
    except ValueError:
        return render(
            request,
            "members/statement.html",
            statement_context(member, form, "Check the month and the date paid."),
            status_code=400,
        )
    message = f"{format_naira(payment.amount_kobo)} recorded for {member.full_name}."
    if payment.late_fee_kobo:
        message += f" Late fee of {format_naira(payment.late_fee_kobo)} applied."
    flash(request, message)
    return RedirectResponse(f"/members/{member.id}", status_code=303)


@router.post("/payments/{payment_id}/delete")
def delete_payment(request: Request, payment: Payment = Depends(payment_or_404), db: Session = Depends(get_db)):
    member_id = payment.member_id
    payment_service.delete_payment(db, payment)
    flash(request, "Payment removed.")
    return RedirectResponse(f"/members/{member_id}", status_code=303)
