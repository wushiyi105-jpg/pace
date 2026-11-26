from __future__ import annotations

import pytest

from pace.domain.guard import check
from pace.domain.rules.zones import fmt, in_zone, table, zone_pace


def test_goal_pace_is_t_zone():
    assert zone_pace(300, "T") == 300


def test_offsets_table():
    t = table(300)
    assert t["E"] == "6:20"
    assert t["M"] == "5:35"
    assert t["I"] == "4:40"
    assert t["R"] == "4:25"


def test_fmt_pads_seconds():
    assert fmt(305) == "5:05"


def test_unknown_zone_raises():
    with pytest.raises(ValueError):
        zone_pace(300, "X")


def test_band_tight_for_t():
    assert in_zone(300, "T", 311) is True
    assert in_zone(300, "T", 315) is False


def test_guard_drops_out_of_band_plane():
    kept, findings = check([{"zone": "I", "pace_sec": 400}], 300)
    assert kept == []
    assert findings[0].rule_id == "guard.pace"


def test_guard_keeps_valid():
    kept, _ = check([{"zone": "E", "pace_sec": 380}], 300)
    assert len(kept) == 1


def test_guard_rejects_garbage_zone():
    _, findings = check([{"zone": "Z", "pace_sec": 300}], 300)
    assert findings
