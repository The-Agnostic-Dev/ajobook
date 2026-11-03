from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import Base, make_engine, make_session_factory
from app.main import create_app
from app.models import Group, Member


@pytest.fixture
def db(tmp_path) -> Session:
    engine = make_engine(f"sqlite:///{tmp_path / 'test.sqlite3'}")
    Base.metadata.create_all(engine)
    session = make_session_factory(engine)()
    yield session
    session.close()
    engine.dispose()


@pytest.fixture
def make_group(db):
    def factory(*, members: int = 4, start: date = date(2026, 1, 1), due_day: int = 5, **kwargs) -> Group:
        group = Group(
            name=kwargs.pop("name", "Test Ajo"),
            contribution_kobo=kwargs.pop("contribution_kobo", 1_000_000),
            start_month=start,
            due_day=due_day,
            grace_days=kwargs.pop("grace_days", 3),
            late_fee_kobo=kwargs.pop("late_fee_kobo", 50_000),
            **kwargs,
        )
        db.add(group)
        for n in range(1, members + 1):
            db.add(Member(group=group, full_name=f"Member {n}", phone=f"0803000000{n}", payout_position=n))
        db.commit()
        return group

    return factory


@pytest.fixture(scope="module")
def client(tmp_path_factory):
    settings = Settings(
        database_url=f"sqlite:///{tmp_path_factory.mktemp('app') / 'app.sqlite3'}", secret_key="test", seed_demo=True
    )
    with TestClient(create_app(settings)) as c:
        yield c


@pytest.fixture(scope="module")
def logged_in(client):
    response = client.post("/login", data={"username": "ngozi", "password": "ajobook2026", "next": "/"})
    assert response.status_code in (200, 303)
    return client
