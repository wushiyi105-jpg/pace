"""新功能：本周课表卡片，坏行只丢自己，不毁整周。"""

from __future__ import annotations

from datetime import date

from typer.testing import CliRunner

from pace.app.run import normalize_sessions
from pace.domain.catalog import pacing, plans
from pace.domain.models import Goal, Session
from pace.iface.cli import app


def test_catalog_has_four_plans_and_eight_injury_rules() -> None:
    assert len(plans()) == 4
    assert len(pacing()["injury_rules"]) == 8
    assert len(pacing()["zones"]) == 5


def test_bad_row_only_drops_itself() -> None:
    planned = [
        Session(1, 1, date(2026, 11, 24), "E", 8),
        Session(2, 1, date(2026, 11, 26), "T", 6),
    ]
    goal = Goal("半马", date(2026, 12, 20), 21.1, 6300)
    raw = [
        {"day": "2026-11-24", "zone": "E", "km": 8},
        {"day": "2026-11-26", "zone": "X", "km": 10},
        {"day": "2026-11-27", "zone": "E", "km": 5},
    ]
    rows, findings, source = normalize_sessions(raw, planned, goal, 1)
    assert source == "model"
    assert any(r["day"] == "2026-11-24" for r in rows)
    assert not any(r["day"] == "2026-11-26" and r["source"] == "model" for r in rows)
    assert findings
    # 被丢的 26 日由原计划补回，整周仍然完整。
    assert any(r["day"] == "2026-11-26" and r["source"] == "plan" for r in rows)


def test_report_cli_writes_md_and_ics(tmp_path) -> None:
    runner = CliRunner()
    db = str(tmp_path / "pace.db")
    assert runner.invoke(app, ["seed", "--db", db]).exit_code == 0
    out = tmp_path / "本周课表.md"
    result = runner.invoke(
        app, ["report", "--db", db, "--week", "1", "--no-llm", "--out", str(out)]
    )
    assert result.exit_code == 0
    body = out.read_text(encoding="utf-8")
    assert "# 本周课表 · 第 1 周" in body
    assert "完成率回顾与下一步" in body
    assert "五区间配速" in body
    assert out.with_suffix(".ics").exists()
