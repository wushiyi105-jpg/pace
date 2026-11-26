"""五区间配速：由目标配速推，不许越过生理边界。"""

from __future__ import annotations

# 相对目标配速的秒数偏移（每公里）
OFFSETS = {"E": 80, "M": 35, "T": 0, "I": -20, "R": -35}
LABELS = {
    "E": "轻松跑",
    "M": "马拉松配速",
    "T": "阈值",
    "I": "间歇",
    "R": "重复跑",
}


def fmt(sec: int) -> str:
    return f"{sec // 60}:{sec % 60:02d}"


def zone_pace(goal_sec: int, zone: str) -> int:
    if zone not in OFFSETS:
        raise ValueError(f"没有这个区间：{zone}")
    return goal_sec + OFFSETS[zone]


def table(goal_sec: int) -> dict[str, str]:
    return {z: fmt(zone_pace(goal_sec, z)) for z in OFFSETS}


def in_zone(goal_sec: int, zone: str, actual_sec: int) -> bool:
    band = 12 if zone in ("T", "I", "R") else 20
    return abs(actual_sec - zone_pace(goal_sec, zone)) <= band
