from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..auth import current_coordinator
from ..db import get_db
from ..services import groups as group_service
from ..services import payments as payment_service
from ..services import summary
from ..templating import render

router = APIRouter(dependencies=[Depends(current_coordinator)])


@router.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    cards = [summary.group_summary(db, g) for g in group_service.list_groups(db)]
    return render(
        request,
        "dashboard.html",
        {"cards": cards, "recent": payment_service.recent_payments(db)},
    )
