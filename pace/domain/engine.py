"""本地核算：周量、完成率、长距离、配速表。"""

from __future__ import annotations

from datetime import date

from .models import Finding, Goal, Review, Session, WeekLoad
from .rules.completion import check as completion_check
from .rules.load import check as load_check
from .rules.race import check as race_check
from .rules.zones import table


def weeks(sessions: list[Session], logs: dict[int, float]) -> list[WeekLoad]:
    out: list[WeekLoad] = []
    for w in sorted({s.week for s in sessions}):
        planned = sum(s.km for s in sessions if s.week == w)
        done = sum(logs.get(s.id, 0.0) for s in sessions if s.week == w)
        out.append(WeekLoad(w, planned, done))
    return out


def plan_of(sessions: list[Session], w: int) -> list[Session]:
    return sorted([s for s in sessions if s.week == w], key=lambda s: s.day)


def review(sessions: list[Session], logs: dict[int, float], goal: Goal | None) -> Review:
    r = Review(goal=goal)
    r.weeks = weeks(sessions, logs)
    findings: list[Finding] = []
    findings += load_check([w.planned for w in r.weeks])
    findings += completion_check(r.weeks)
    if goal:
        findings += race_check(sessions, goal.distance_km)
    r.findings = findings
    return r


def zone_table(goal: Goal) -> dict[str, str]:
    return table(goal.pace_sec)


def replan(sessions: list[Session], r: Review) -> list[dict[str, object]]:
    """把低于 60% 的周之后两周总量降下来，返回建议（不改库）。"""
    slow = {w.week for w in r.weeks if w.planned and w.rate < 0.60}
    out: list[dict[str, object]] = []
    for w in sorted(slow):
        base = next((x.planned for x in r.weeks if x.week == w + 1), 0.0)
        out.append({"week": w + 1, "planned_before": base, "planned_after": round(base * 0.9, 1)})
    return out


def days_left(goal: Goal, today: date) -> int:
    return (goal.race_on - today).days
