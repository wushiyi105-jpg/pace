"""配速守卫：模型给的配速必须落在区间内，否则丢弃。"""

from __future__ import annotations

from .models import Finding
from .rules.zones import in_zone

PENALTY = 6


def check(items: list[dict], goal_sec: int) -> tuple[list[dict], list[Finding]]:
    kept: list[dict] = []
    findings: list[Finding] = []
    for it in items:
        zone = str(it.get("zone", ""))
        try:
            pace = int(it.get("pace_sec", -1))
        except (TypeError, ValueError):
            pace = -1
        if zone not in ("E", "M", "T", "I", "R") or pace < 0:
            findings.append(Finding("guard.pace", f"区间或配速不合法：{it}", PENALTY, zone))
            continue
        if not in_zone(goal_sec, zone, pace):
            findings.append(
                Finding("guard.pace", f"{zone} 区间给的 {pace} 秒/公里不在允许带内，丢弃", PENALTY, zone)
            )
            continue
        kept.append(it)
    return kept, findings
