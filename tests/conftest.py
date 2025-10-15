import os
from pathlib import Path

TEST_DB_PATH = Path("test_smart_resume.db")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH.as_posix()}")

from app.database import Base, engine  # noqa: E402 - import after env var setup

import pytest


def _reset_database() -> None:
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def pytest_sessionstart(session):  # noqa: D401 - pytest hook
    _reset_database()


def pytest_sessionfinish(session, exitstatus):  # noqa: D401 - pytest hook
    engine.dispose()
    if TEST_DB_PATH.exists():
        TEST_DB_PATH.unlink()


@pytest.fixture(autouse=True)
def _db_cleanup():
    _reset_database()
    yield
    _reset_database()
