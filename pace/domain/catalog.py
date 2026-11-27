"""4 套周期模板、5 区间、8 条伤病减量规则。"""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]


@lru_cache(maxsize=1)
def plans() -> list[dict[str, Any]]:
    return json.loads((ROOT / "data" / "plan_templates.json").read_text(encoding="utf-8"))["templates"]


@lru_cache(maxsize=1)
def pacing() -> dict[str, Any]:
    return json.loads((ROOT / "data" / "pacing_rules.json").read_text(encoding="utf-8"))


def template_for(distance_km: float) -> dict[str, Any]:
    if distance_km <= 6:
        return plans()[0]
    if distance_km <= 11:
        return plans()[1]
    if distance_km <= 25:
        return plans()[2]
    return plans()[3]


def pattern_for(distance_km: float, week: int) -> list[tuple[str, float]]:
    template = template_for(distance_km)
    for phase in template["phases"]:
        if phase["week_from"] <= week <= phase["week_to"]:
            return [(str(z), float(km)) for z, km in phase["sessions"]]
    last = template["phases"][-1]
    return [(str(z), float(km)) for z, km in last["sessions"]]
