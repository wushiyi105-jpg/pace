"""真实内存 Store 跑 current：不建 SQLite，mypy 校验 StorePort。"""

from __future__ import annotations

from pace.app.run import current
from pace.domain.models import Goal, Session
from pace.ports import StorePort


class InMemoryStore:
    def goal(self) -> Goal | None:
        return None

    def list_sessions(self) -> list[Session]:
        return []

    def done_map(self) -> dict[int, float]:
        return {}


def test_current_with_memory_store() -> None:
    store: StorePort = InMemoryStore()
    out = current(store)
    assert out.weeks == []
