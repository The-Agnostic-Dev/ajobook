import re
from html.parser import HTMLParser


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


def test_payout_rotation_numbered_from_one(logged_in):
    dashboard = logged_in.get("/").text
    match = re.search(r'href="(/groups/\d+)"[^>]*>\s*Balogun Market Traders Ajo', dashboard)
    assert match, "dashboard should link to the Balogun Market group"
    page = logged_in.get(match.group(1)).text

    rows = []

    class RotationParser(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_table = False
            self.in_cell = False
            self.current = {}
            self.buffer = ""

        def handle_starttag(self, tag, attrs):
            attrs = dict(attrs)
            if tag == "table" and attrs.get("data-testid") == "rotation":
                self.in_table = True
            elif self.in_table and tag == "tr":
                self.current = {}
            elif self.in_table and tag == "td":
                self.in_cell = True
                self.buffer = ""
                self.cell_class = attrs.get("class", "")

        def handle_data(self, data):
            if self.in_cell:
                self.buffer += data

        def handle_endtag(self, tag):
            if tag == "table" and self.in_table:
                self.in_table = False
            elif self.in_table and tag == "td" and self.in_cell:
                self.in_cell = False
                if "position" in self.cell_class:
                    self.current["position"] = self.buffer.strip()
                elif "name" in self.cell_class:
                    self.current["name"] = self.buffer.strip()
            elif self.in_table and tag == "tr":
                if self.current:
                    rows.append(self.current)

    parser = RotationParser()
    parser.feed(page)

    positions = [row["position"] for row in rows]
    assert positions == [str(n) for n in range(1, 11)]
    assert "0" not in positions
    names = [row["name"] for row in rows]
    assert names[0] == "Adunni Bakare"
    assert names[9] == "Uche Obi"


def test_member_search(logged_in):
    response = logged_in.get("/members", params={"q": "kunle"})
    assert "Kunle Adeyemi" in response.text


def test_resending_the_same_form_records_once(logged_in):
    data = {"cycle": "1", "amount": "750", "paid_on": "2026-01-02", "note": "Sent twice", "form_token": "tok-1"}
    first = logged_in.post("/members/2/payments", data=data)
    second = logged_in.post("/members/2/payments", data=data)
    assert "recorded for" in first.text
    assert "already recorded" in second.text
    assert second.text.count("Sent twice") == 1
