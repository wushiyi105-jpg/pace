"""周量增幅：相邻两周超过 10% 提醒。"""

from __future__ import annotations

from ..models import Finding

LIMIT = 0.10
PENALTY = 6


def check(planned: list[float]) -> list[Finding]:
    out: list[Finding] = []
    for i in range(1, len(planned)):
        prev, cur = planned[i - 1], planned[i]
        if prev <= 0:
            continue
        growth = (cur - prev) / prev
        if growth > LIMIT:
            out.append(
                Finding(
                    "load.increase",
                    f"第 {i + 1} 周 {cur:g} 公里，比上一周 {prev:g} 涨了 {growth:.0%}，超过 10%",
                    PENALTY,
                    str(i + 1),
                )
            )
    return out
