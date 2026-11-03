from pathlib import Path

from fastapi import Request
from fastapi.templating import Jinja2Templates

from .auth import pop_flashes
from .dates import lagos_today, long_date, month_label
from .money import format_naira, naira_input

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")
templates.env.filters["naira"] = format_naira
templates.env.filters["naira_input"] = naira_input
templates.env.filters["longdate"] = long_date
templates.env.filters["monthlabel"] = month_label


def render(request: Request, name: str, context: dict | None = None, status_code: int = 200):
    context = dict(context or {})
    context.setdefault("today", lagos_today())
    context["flashes"] = pop_flashes(request)
    context["coordinator_name"] = request.session.get("coordinator_name")
    return templates.TemplateResponse(request, name, context, status_code=status_code)
