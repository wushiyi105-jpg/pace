"""领域对象：目标、周计划、单次课、完成记录。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

ZONES = ("E", "M", "T", "I", "R")


@dataclass(frozen=True)
class Goal:
    race: str
    race_on: date
    distance_km: float
    target_sec: int

    @property
    def pace_sec(self) -> int:
        return int(round(self.target_sec / self.distance_km))


@dataclass(frozen=True)
class Session:
    id: int
    week: int
    day: date
    zone: str
    km: float


@dataclass(frozen=True)
class Log:
    id: int
    session_id: int
    km: float
    rpe: int


@dataclass
class Finding:
    rule_id: str
    message: str
    penalty: int
    target: str = ""


@dataclass
class WeekLoad:
    week: int
    planned: float
    done: float

    @property
    def rate(self) -> float:
        return self.done / self.planned if self.planned else 1.0


@dataclass
class Review:
    goal: Goal | None = None
    weeks: list[WeekLoad] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)

    @property
    def penalty_total(self) -> int:
        return sum(f.penalty for f in self.findings)
