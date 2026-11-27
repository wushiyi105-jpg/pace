"""用例：复盘 → 模型下周课表 → 守卫 → 重排建议。"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path
from typing import TypedDict

from ..config import Settings
from ..domain.catalog import pacing, pattern_for
from ..domain.engine import days_left, replan, review, zone_table
from ..domain.ics import build as ics_build
from ..domain.models import Finding, Goal, Review, Session
from ..domain.rules.zones import zone_pace
from ..ports import LLMPort, StorePort

PROMPT = (Path(__file__).resolve().parents[2] / "prompts" / "coach.md").read_text(encoding="utf-8")
VALID_ZONES = {"E", "M", "T", "I", "R"}


class WeekRow(TypedDict):
    id: int
    week: int
    day: str
    zone: str
    km: float
    pace_sec: int
    source: str


def current(store: StorePort) -> Review:
    return review(store.list_sessions(), store.done_map(), store.goal())


def _local_rows(sessions: list[Session], goal: Goal, week: int) -> list[WeekRow]:
    return [
        {
            "id": s.id,
            "week": week,
            "day": s.day.isoformat(),
            "zone": s.zone,
            "km": s.km,
            "pace_sec": zone_pace(goal.pace_sec, s.zone),
            "source": "plan",
        }
        for s in sorted(sessions, key=lambda x: x.day)
    ]


def normalize_sessions(
    raw: list[dict],
    planned: list[Session],
    goal: Goal,
    week: int,
) -> tuple[list[WeekRow], list[Finding], str]:
    """模型只填日期/区间/公里；配速由本地区间表补，坏行丢掉不毁整周。"""
    allowed_days = {s.day for s in planned}
    rows: list[WeekRow] = []
    findings: list[Finding] = []
    for item in raw:
        zone = str(item.get("zone", "")).upper()
        day_s = str(item.get("day", ""))
        try:
            day = date.fromisoformat(day_s)
            km = float(item.get("km", 0))
        except (TypeError, ValueError):
            findings.append(Finding("plan.bad_row", f"课表行不合法，已丢：{item}", 2, day_s))
            continue
        if zone not in VALID_ZONES or not 0.5 <= km <= 60:
            findings.append(Finding("plan.bad_row", f"区间或公里不合法，已丢：{item}", 2, zone))
            continue
        if allowed_days and day not in allowed_days:
            findings.append(Finding("plan.bad_date", f"{day} 不在第 {week} 周计划里，已丢", 2, day_s))
            continue
        rows.append(
            {
                "id": -len(rows) - 1,
                "week": week,
                "day": day.isoformat(),
                "zone": zone,
                "km": km,
                "pace_sec": zone_pace(goal.pace_sec, zone),
                "source": "model",
            }
        )
    if not rows:
        return _local_rows(planned, goal, week), findings, "plan"
    # 模型只给了两天时，其余天用原计划补齐，不把整周变成空白。
    covered = {str(r["day"]) for r in rows}
    for local in _local_rows(planned, goal, week):
        if str(local["day"]) not in covered:
            rows.append(local)
    rows.sort(key=lambda r: str(r["day"]))
    return rows, findings, "model"


def build_week(
    store: StorePort, settings: Settings, week: int, llm: LLMPort | None = None
) -> tuple[list[WeekRow], list[Finding], str]:
    goal = store.goal()
    if goal is None:
        return [], [], "plan"
    planned = [s for s in store.list_sessions() if s.week == week]
    if not planned:
        monday = date.today() - timedelta(days=date.today().weekday())
        pattern = pattern_for(goal.distance_km, week)
        offsets = [1, 3, 6, 2, 5][: len(pattern)]
        planned = [
            Session(-i - 1, week, monday + timedelta(days=offsets[i]), zone, km)
            for i, (zone, km) in enumerate(pattern)
        ]
    r = current(store)
    facts = {
        "week": week,
        "race": goal.race,
        "distance_km": goal.distance_km,
        "days_left": days_left(goal, date.today()),
        "zones": zone_table(goal),
        "planned": [
            {"day": s.day.isoformat(), "zone": s.zone, "km": s.km} for s in planned
        ],
        "weeks": [{"week": w.week, "planned": w.planned, "done": w.done} for w in r.weeks],
        "replan": replan(store.list_sessions(), r),
    }
    if llm is None:
        return _local_rows(planned, goal, week), [], "plan"
    try:
        data = json.loads(llm.write(PROMPT, json.dumps(facts, ensure_ascii=False)))
    except Exception:  # noqa: BLE001
        return _local_rows(planned, goal, week), [], "plan"
    return normalize_sessions(list(data.get("sessions", [])), planned, goal, week)


def suggest(
    store: StorePort, settings: Settings, llm: LLMPort | None = None
) -> tuple[list[WeekRow], list[Finding]]:
    goal = store.goal()
    if goal is None:
        return [], []
    weeks = {s.week for s in store.list_sessions()}
    week = max(weeks) if weeks else 1
    rows, findings, _ = build_week(store, settings, week, llm)
    return rows, findings


def zones() -> dict[str, str]:
    return {z["code"]: z["name"] for z in pacing()["zones"]}


def export(store: StorePort, week: int) -> str:
    goal = store.goal()
    if goal is None:
        raise ValueError("先设目标")
    return ics_build([s for s in store.list_sessions() if s.week == week], goal.pace_sec)
