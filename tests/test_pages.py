import re


def test_pages_need_login(client):
    response = client.get("/groups/1", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"].startswith("/login")


def test_wrong_password(client):
    response = client.post("/login", data={"username": "ngozi", "password": "nope"})
    assert response.status_code == 400
    assert "Wrong username or password" in response.text


def test_dashboard_lists_demo_groups(logged_in):
    page = logged_in.get("/").text
    for name in ("Balogun Market Traders Ajo", "Ministry of Works Staff Esusu", "Ikeja Food Sellers Ajo"):
        assert name in page


def test_group_pages_render(logged_in):
    for path in ("/groups/1", "/groups/1/schedule", "/groups/1/payments", "/groups/1/payout", "/groups/1/edit"):
        assert logged_in.get(path).status_code == 200, path


def test_create_group(logged_in):
    response = logged_in.post(
        "/groups/new",
        data={
            "name": "Yaba Tailors Ajo",
            "contribution": "15,000",
            "start_month": "2026-01",
            "due_day": "10",
            "grace_days": "2",
            "late_fee": "500",
        },
    )
    assert response.status_code == 200
    assert "Yaba Tailors Ajo" in response.text
    assert "₦15,000.00" in response.text


def test_create_group_validation(logged_in):
    response = logged_in.post("/groups/new", data={"name": "", "contribution": "abc", "start_month": "2026-01"})
    assert response.status_code == 400
    assert "Give the group a name." in response.text


def test_record_payment_from_statement(logged_in):
    page = logged_in.get("/members/1")
    assert page.status_code == 200
    response = logged_in.post(
        "/members/1/payments",
        data={"cycle": "1", "amount": "1,000", "paid_on": "2026-01-01", "note": "Pytest top-up"},
    )
    assert response.status_code == 200
    assert "₦1,000.00 recorded" in response.text


def test_record_payment_rejects_bad_amount(logged_in):
    response = logged_in.post("/members/1/payments", data={"cycle": "1", "amount": "abc", "paid_on": "2026-01-01"})
    assert response.status_code == 400
    assert "is not an amount" in response.text


def test_member_search(logged_in):
    response = logged_in.get("/members", params={"q": "kunle"})
    assert "Kunle Adeyemi" in response.text


def test_payout_rotation_positions_start_at_one(logged_in):
    dashboard = logged_in.get("/").text
    assert "Balogun Market Traders Ajo" in dashboard

    page = logged_in.get("/groups/1").text
    table = page.split("Payout rotation", 1)[1].split("</table>", 1)[0]
    positions = [int(n) for n in re.findall(r'<td class="position">\s*(\d+)\s*</td>', table)]
    assert positions == list(range(1, 11))

    member_ids = re.findall(r'href="/members/(\d+)"', table)
    assert len(member_ids) == 10
    for position, member_id in enumerate(member_ids, start=1):
        statement = logged_in.get(f"/members/{member_id}").text
        turn = re.search(r"Payout turn.*?(\d+)", statement, re.DOTALL)
        assert turn, member_id
        assert int(turn.group(1)) == position


def test_resending_the_same_form_records_once(logged_in):
    data = {"cycle": "1", "amount": "750", "paid_on": "2026-01-02", "note": "Sent twice", "form_token": "tok-1"}
    first = logged_in.post("/members/2/payments", data=data)
    second = logged_in.post("/members/2/payments", data=data)
    assert "recorded for" in first.text
    assert "already recorded" in second.text
    assert second.text.count("Sent twice") == 1
