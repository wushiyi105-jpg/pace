"""导出 ICS：一周的课表直接进日历。"""

from __future__ import annotations

from datetime import datetime, timezone

from .models import Session
from .rules.zones import LABELS, zone_pace


def _stamp(d: datetime) -> str:
    return d.strftime("%Y%m%dT%H%M%SZ")


def build(sessions: list[Session], goal_sec: int) -> str:
    lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//pace//zh//CN", "CALSCALE:GREGORIAN"]
    for s in sessions:
        start = datetime(s.day.year, s.day.month, s.day.day, 22, 0, tzinfo=timezone.utc)
        end = start.replace(hour=23, minute=0)
        lines += [
            "BEGIN:VEVENT",
            f"UID:pace-{s.id}@local",
            f"DTSTAMP:{_stamp(datetime.now(timezone.utc))}",
            f"DTSTART:{_stamp(start)}",
            f"DTEND:{_stamp(end)}",
            f"SUMMARY:{LABELS[s.zone]} {s.km:g} 公里",
            f"DESCRIPTION:{s.km:g} 公里 @ {zone_pace(goal_sec, s.zone) // 60}:{zone_pace(goal_sec, s.zone) % 60:02d}/公里",
            "END:VEVENT",
        ]
    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"
