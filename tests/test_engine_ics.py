from __future__ import annotations

from datetime import date

from pace.domain.engine import days_left, replan, review, zone_table
from pace.domain.ics import build


def _seed(store):
    store.add_session(1, date(2026, 11, 24), "E", 8)
    store.add_session(1, date(2026, 11, 26), "T", 6)
    store.add_session(2, date(2026, 12, 1), "E", 10)


def test_review_weeks_and_rates(store, goal):
    _seed(store)
    store.log(1, 8)
    store.log(2, 3)
    r = review(store.list_sessions(), store.done_map(), goal)
    assert r.weeks[0].rate > 0.7
    assert r.weeks[1].rate == 0


def test_long_run_needs_seventy_percent(store, goal):
    _seed(store)
    r = review(store.list_sessions(), {}, goal)
    assert any(f.rule_id == "race.long" for f in r.findings)


def test_long_run_enough_no_finding(store, goal):
    store.add_session(1, date(2026, 11, 30), "E", 15)
    r = review(store.list_sessions(), {}, goal)
    assert not any(f.rule_id == "race.long" for f in r.findings)


def test_days_left(goal):
    assert days_left(goal, date(2026, 12, 10)) == 10


def test_zone_table_from_goal(goal):
    assert zone_table(goal)["T"] == "4:59"


def test_replan_suggests_ninety_percent(store, goal):
    store.add_session(1, date(2026, 11, 24), "E", 20)
    store.add_session(2, date(2026, 12, 1), "E", 30)
    store.log(1, 5)
    store.log(2, 5)
    r = review(store.list_sessions(), store.done_map(), goal)
    rows = replan(store.list_sessions(), r)
    assert rows[0]["planned_after"] == 27.0


def test_ics_contains_events(store, goal):
    _seed(store)
    text = build(store.list_sessions(), goal.pace_sec)
    assert text.count("BEGIN:VEVENT") == 3
    assert "轻松跑" in text
    assert text.endswith("\r\n")
