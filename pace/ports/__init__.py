"""端口：app 实际调用的方法集合，实现见 adapters。"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from ..domain.models import Goal, Session


@runtime_checkable
class StorePort(Protocol):
    def goal(self) -> Goal | None: ...

    def list_sessions(self) -> list[Session]: ...

    def done_map(self) -> dict[int, float]: ...


@runtime_checkable
class LLMPort(Protocol):
    def write(self, system: str, facts: str) -> str: ...
