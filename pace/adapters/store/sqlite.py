"""SQLite：goals / sessions / logs / jobs。"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from sqlalchemy import Date, Float, Integer, String, inspect, select
from sqlalchemy.orm import Mapped, mapped_column, sessionmaker
from sqlalchemy.orm import Session as OrmSession

from ...domain.models import Goal, Log, Session
from .base import Base, make_engine, make_session


class GoalRow(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    race: Mapped[str] = mapped_column(String(60))
    race_on: Mapped[date] = mapped_column(Date)
    distance_km: Mapped[float] = mapped_column(Float)
    target_sec: Mapped[int] = mapped_column(Integer)


class SessionRow(Base):
    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    week: Mapped[int] = mapped_column(Integer)
    day: Mapped[date] = mapped_column(Date)
    zone: Mapped[str] = mapped_column(String(4))
    km: Mapped[float] = mapped_column(Float)


class LogRow(Base):
    __tablename__ = "logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    session_id: Mapped[int] = mapped_column(Integer)
    km: Mapped[float] = mapped_column(Float)
    rpe: Mapped[int] = mapped_column(Integer, default=5)


class JobRow(Base):
    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    idem_key: Mapped[str] = mapped_column(String(80), unique=True)
    payload: Mapped[str] = mapped_column(String(200), default="")


class SqliteStore:
    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)
        self.engine = make_engine(self.path)
        self.session: sessionmaker[OrmSession] = make_session(self.engine)
        Base.metadata.create_all(self.engine)

    def init_schema(self) -> None:
        Base.metadata.create_all(self.engine)

    def schema_ok(self) -> bool:
        return {"goals", "sessions", "logs", "jobs"} <= set(inspect(self.engine).get_table_names())

    def summary(self) -> str:
        return f"{len(self.list_sessions())} 次课、{len(self.list_logs())} 条完成记录"

    def set_goal(self, race: str, race_on: date, distance_km: float, target_sec: int) -> int:
        if distance_km <= 0 or target_sec <= 0:
            raise ValueError("距离与目标时间都要大于 0")
        with self.session() as s:
            row = GoalRow(race=race, race_on=race_on, distance_km=distance_km, target_sec=target_sec)
            s.add(row)
            s.commit()
            return int(row.id)

    def goal(self) -> Goal | None:
        with self.session() as s:
            row = s.scalars(select(GoalRow).order_by(GoalRow.id.desc())).first()
        if row is None:
            return None
        return Goal(row.race, row.race_on, float(row.distance_km), int(row.target_sec))

    def add_session(self, week: int, day: date, zone: str, km: float) -> int:
        if zone not in ("E", "M", "T", "I", "R"):
            raise ValueError(f"没有这个区间：{zone}")
        if km <= 0:
            raise ValueError("距离要大于 0")
        with self.session() as s:
            row = SessionRow(week=week, day=day, zone=zone, km=km)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_sessions(self) -> list[Session]:
        with self.session() as s:
            rows = s.scalars(select(SessionRow).order_by(SessionRow.day)).all()
        return [Session(r.id, r.week, r.day, r.zone, float(r.km)) for r in rows]

    def log(self, session_id: int, km: float, rpe: int = 5) -> int:
        if not 1 <= rpe <= 10:
            raise ValueError("RPE 要在 1-10")
        with self.session() as s:
            row = LogRow(session_id=session_id, km=km, rpe=rpe)
            s.add(row)
            s.commit()
            return int(row.id)

    def list_logs(self) -> list[Log]:
        with self.session() as s:
            rows = s.scalars(select(LogRow)).all()
        return [Log(r.id, r.session_id, float(r.km), r.rpe) for r in rows]

    def done_map(self) -> dict[int, float]:
        out: dict[int, float] = {}
        for row in self.list_logs():
            out[row.session_id] = out.get(row.session_id, 0.0) + row.km
        return out

    def add_job(self, idem_key: str, payload: str = "") -> bool:
        with self.session() as s:
            if s.scalars(select(JobRow).where(JobRow.idem_key == idem_key)).first():
                return False
            s.add(JobRow(idem_key=idem_key, payload=payload))
            s.commit()
            return True
