"""Naira amounts are stored as whole kobo (int) everywhere. These helpers convert at the edges."""

from decimal import Decimal, InvalidOperation


class AmountError(ValueError):
    pass


def parse_naira(raw: str) -> int:
    """Turn what a coordinator types ("20,000", "₦20,000.50", "20000") into kobo."""
    cleaned = (raw or "").strip().replace("₦", "").replace("NGN", "").replace(",", "").replace(" ", "")
    if not cleaned:
        raise AmountError("Enter an amount.")
    try:
        value = Decimal(cleaned)
    except InvalidOperation as exc:
        raise AmountError(f"“{raw}” is not an amount.") from exc
    if value.as_tuple().exponent < -2:
        raise AmountError("Amounts can have at most two decimal places (kobo).")
    return int(value * 100)


def format_naira(kobo: int | None) -> str:
    kobo = kobo or 0
    sign = "-" if kobo < 0 else ""
    naira, rem = divmod(abs(kobo), 100)
    return f"{sign}₦{naira:,}.{rem:02d}"


def naira_input(kobo: int | None) -> str:
    """Plain value for an <input>, e.g. 2000000 -> "20,000"."""
    kobo = kobo or 0
    naira, rem = divmod(kobo, 100)
    return f"{naira:,}" if rem == 0 else f"{naira:,}.{rem:02d}"
