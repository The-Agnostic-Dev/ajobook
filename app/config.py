import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

LAGOS = ZoneInfo("Africa/Lagos")


@dataclass(frozen=True)
class Settings:
    database_url: str
    secret_key: str
    seed_demo: bool


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv("AJOBOOK_DATABASE_URL", "sqlite:///./ajobook.sqlite3"),
        secret_key=os.getenv("AJOBOOK_SECRET_KEY", "dev-secret-change-me"),
        seed_demo=os.getenv("AJOBOOK_SEED_DEMO", "1") == "1",
    )
