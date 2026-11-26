"""用例：复盘 → 模型下周课表 → 守卫 → 重排建议。"""

from __future__ import annotations

import json
from datetime import date

from ..adapters.llm import build_llm
from ..adapters.store import SqliteStore
from ..config import Settings
from ..domain.engine import days_left, replan, review, zone_table
from ..domain.guard import check
from ..domain.ics import build as ics_build
from ..domain.models import Finding, Review

PROMPT = """给下一周训练课表，输出 JSON：
{"sessions": [{"day": "YYYY-MM-DD", "zone": "E|M|T|I|R", "km": 8, "pace_sec": 380}]}
规则：周总量比上周涨幅不超过 10%；配速必须落在给定区间的允许带内；只报数字，不承诺成绩。"""


def current(store: SqliteStore) -> Review:
    return review(store.list_sessions(), store.done_map(), store.goal())


def suggest(store: SqliteStore, settings: Settings) -> tuple[list[dict], list[Finding]]:
    goal = store.goal()
    if goal is None or not settings.llm_enabled:
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
    llm = build_llm(settings.llm_base_url, settings.llm_api_key, settings.llm_model, PROMPT)
    try:
        data = json.loads(llm.write(PROMPT, json.dumps(facts, ensure_ascii=False)))
    except Exception:  # noqa: BLE001
        return [], []
    return check(list(data.get("sessions", [])), goal.pace_sec)


def export(store: SqliteStore, week: int) -> str:
    goal = store.goal()
    if goal is None:
        raise ValueError("先设目标")
    return ics_build([s for s in store.list_sessions() if s.week == week], goal.pace_sec)
