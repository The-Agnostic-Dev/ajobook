from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import flash, verify_password
from ..db import get_db
from ..models import Coordinator
from ..templating import render

router = APIRouter()


def _safe_next(target: str | None) -> str:
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return "/"


@router.get("/login")
def login_form(request: Request, next: str = "/"):
    return render(request, "login.html", {"next": _safe_next(next), "username": ""})


@router.post("/login")
def login(
    request: Request,
    username: str = Form(""),
    password: str = Form(""),
    next: str = Form("/"),
    db: Session = Depends(get_db),
):
    coordinator = db.scalar(select(Coordinator).where(Coordinator.username == username.strip().lower()))
    if coordinator is None or not verify_password(password, coordinator.password_hash):
        return render(
            request,
            "login.html",
            {"next": _safe_next(next), "username": username, "error": "Wrong username or password."},
            status_code=400,
        )
    request.session["coordinator_id"] = coordinator.id
    request.session["coordinator_name"] = coordinator.full_name
    return RedirectResponse(_safe_next(next), status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    flash(request, "You have logged out.")
    return RedirectResponse("/login", status_code=303)
