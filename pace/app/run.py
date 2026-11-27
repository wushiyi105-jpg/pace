"""用例：复盘 → 模型下周课表 → 守卫 → 重排建议。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from ..config import Settings
from ..domain.engine import days_left, replan, review, zone_table
from ..domain.guard import check
from ..domain.ics import build as ics_build
from ..domain.models import Finding, Review
from ..ports import LLMPort, StorePort

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "coach.md").read_text(encoding="utf-8")


def current(store: StorePort) -> Review:
    return review(store.list_sessions(), store.done_map(), store.goal())


def suggest(
    store: StorePort, settings: Settings, llm: LLMPort | None = None
) -> tuple[list[dict], list[Finding]]:
    goal = store.goal()
    if goal is None or llm is None:
        return [], []
    r = current(store)
    table = zone_table(goal)
    facts = {
        "race": goal.race,
        "distance_km": goal.distance_km,
        "days_left": days_left(goal, date.today()),
        "zones": table,
        "weeks": [{"week": w.week, "planned": w.planned, "done": w.done} for w in r.weeks],
        "replan": replan(store.list_sessions(), r),
    }
    try:
        data = json.loads(llm.write(PROMPT, json.dumps(facts, ensure_ascii=False)))
    except Exception:  # noqa: BLE001
        return [], []
    return check(list(data.get("sessions", [])), goal.pace_sec)


def export(store: StorePort, week: int) -> str:
    goal = store.goal()
    if goal is None:
        raise ValueError("先设目标")
    return ics_build([s for s in store.list_sessions() if s.week == week], goal.pace_sec)
