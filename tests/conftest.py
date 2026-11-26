from __future__ import annotations

import pytest

from pace.adapters.store import SqliteStore
from pace.config import Settings


@pytest.fixture()
def store(tmp_path) -> SqliteStore:
    return SqliteStore(tmp_path / "t.db")


@pytest.fixture()
def settings(tmp_path) -> Settings:
    return Settings(db_path=tmp_path / "t.db", llm_api_key="", port=8014)


@pytest.fixture()
def goal(store):
    store.set_goal("半马", __import__("datetime").date(2026, 12, 20), 21.1, 6300)
    return store.goal()
