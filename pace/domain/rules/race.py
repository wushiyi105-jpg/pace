"""赛前长距离：最长一次要跑到比赛距离的 70%。"""

from __future__ import annotations

from ..models import Finding, Session

SHARE = 0.70
PENALTY = 5


def longest(sessions: list[Session]) -> float:
    return max((s.km for s in sessions), default=0.0)


def check(sessions: list[Session], distance_km: float) -> list[Finding]:
    need = distance_km * SHARE
    got = longest(sessions)
    if got >= need:
        return []
    return [
        Finding(
            "race.long",
            f"最长一次 {got:g} 公里，{distance_km:g} 公里比赛至少要 {need:.1f} 公里",
            PENALTY,
            "long",
        )
    ]
