import hashlib
import hmac
import secrets

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from .db import get_db
from .models import Coordinator

_ITERATIONS = 120_000


class LoginRequired(Exception):
    def __init__(self, next_path: str = "/"):
        self.next_path = next_path


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(8)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), _ITERATIONS).hex()
    return f"pbkdf2${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, _digest = stored.split("$")
    except ValueError:
        return False
    return hmac.compare_digest(hash_password(password, salt), stored)


def current_coordinator(request: Request, db: Session = Depends(get_db)) -> Coordinator:
    coordinator_id = request.session.get("coordinator_id")
    coordinator = db.get(Coordinator, coordinator_id) if coordinator_id else None
    if coordinator is None:
        raise LoginRequired(request.url.path)
    return coordinator


def flash(request: Request, message: str, kind: str = "ok") -> None:
    request.session.setdefault("flashes", []).append({"message": message, "kind": kind})


def pop_flashes(request: Request) -> list[dict[str, str]]:
    return request.session.pop("flashes", [])
