import pytest

from app.money import AmountError, format_naira, naira_input, parse_naira


@pytest.mark.parametrize(
    ("raw", "kobo"),
    [("20000", 2_000_000), ("20,000", 2_000_000), ("₦20,000.50", 2_000_050), (" 1,250.5 ", 125_050), ("0", 0)],
)
def test_parse_naira(raw, kobo):
    assert parse_naira(raw) == kobo


@pytest.mark.parametrize("raw", ["", "abc", "12.345"])
def test_parse_naira_rejects(raw):
    with pytest.raises(AmountError):
        parse_naira(raw)


def test_format_naira():
    assert format_naira(1_250_000) == "₦12,500.00"
    assert format_naira(5) == "₦0.05"
    assert format_naira(-150_000) == "-₦1,500.00"
    assert format_naira(None) == "₦0.00"


def test_naira_input():
    assert naira_input(2_000_000) == "20,000"
    assert naira_input(2_000_050) == "20,000.50"
