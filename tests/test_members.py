import pytest

from app.services import members


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("0803 123 4567", "08031234567"), ("+234 803 123 4567", "08031234567"), ("234-803-123-4567", "08031234567")],
)
def test_normalize_phone(raw, expected):
    assert members.normalize_phone(raw) == expected


def test_parse_form_rejects_bad_phone():
    with pytest.raises(members.MemberFormError) as err:
        members.parse_form({"full_name": "Ada Obi", "phone": "12345"})
    assert "phone" in err.value.errors


def test_new_member_joins_at_the_end(db, make_group):
    group = make_group(members=3)
    member = members.add_member(db, group, members.parse_form({"full_name": "Ada  Obi", "phone": "0803 555 0000"}))
    assert member.payout_position == 4
    assert member.full_name == "Ada Obi"


def test_removing_a_member_closes_the_gap(db, make_group):
    group = make_group(members=4)
    members.remove_member(db, group.members[1])
    db.refresh(group)
    assert [(m.full_name, m.payout_position) for m in group.members] == [
        ("Member 1", 1),
        ("Member 3", 2),
        ("Member 4", 3),
    ]


def test_search_by_name_and_phone(db, make_group):
    make_group(members=3)
    assert [m.full_name for m in members.search(db, "member 2")] == ["Member 2"]
    assert [m.full_name for m in members.search(db, "08030000003")] == ["Member 3"]
