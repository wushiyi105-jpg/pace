"""完成率：连续两周低于 60% 就重排，不是硬顶。"""

from __future__ import annotations

from ..models import Finding, WeekLoad

FLOOR = 0.60
PENALTY = 8
STREAK = 2


def low_weeks(weeks: list[WeekLoad]) -> list[int]:
    return [w.week for w in weeks if w.planned > 0 and w.rate < FLOOR]


def streak(weeks: list[WeekLoad]) -> list[int]:
    slow = low_weeks(weeks)
    run: list[int] = []
    best: list[int] = []
    prev = None
    for w in slow:
        if prev is not None and w == prev + 1:
            run.append(w)
        else:
            run = [w]
        if len(run) > len(best):
            best = list(run)
        prev = w
    return best if len(best) >= STREAK else []


def check(weeks: list[WeekLoad]) -> list[Finding]:
    s = streak(weeks)
    if not s:
        return []
    return [
        Finding(
            "plan.replan",
            f"第 {'、'.join(str(x) for x in s)} 周连续低于 60%，下两周总量下调到 {int(FLOOR * 100)}%",
            PENALTY,
            ",".join(str(x) for x in s),
        )
    ]
