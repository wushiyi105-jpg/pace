"""主用例只依赖 ports：用 MagicMock 内存假实现，不建 SQLite 文件。"""

from __future__ import annotations

from unittest.mock import MagicMock

from pace.app.run import current
from pace.ports import StorePort


def test_main_path_with_memory_store(tmp_path) -> None:
    store = MagicMock(spec=StorePort)
    store.goal.return_value = None
    store.list_sessions.return_value = []
    store.done_map.return_value = {}
    
    out = current(store)
    assert out is not None
    assert not (tmp_path / "app.db").exists()
