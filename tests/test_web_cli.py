from __future__ import annotations

from datetime import date

from fastapi.testclient import TestClient
from typer.testing import CliRunner

from pace.doctor import run_doctor
from pace.iface.cli import app
from pace.iface.web import create_app


def _seed(store):
    store.set_goal("半马", date(2026, 12, 20), 21.1, 6300)
    store.add_session(1, date(2026, 11, 24), "E", 8)


def test_index(store, settings):
    _seed(store)
    client = TestClient(create_app(settings, store))
    body = client.get("/").text
    assert client.get("/").status_code == 200
    assert "五区间配速" in body


def test_ics_route(store, settings):
    _seed(store)
    r = TestClient(create_app(settings, store)).get("/week/1.ics")
    assert r.status_code == 200
    assert "BEGIN:VCALENDAR" in r.text


def test_ics_route_without_goal(store, settings):
    assert TestClient(create_app(settings, store)).get("/week/1.ics").status_code == 404


def test_cli_cli_week_missing(tmp_path):
    runner = CliRunner()
    db = str(tmp_path / "c.db")
    assert runner.invoke(app, ["week", "--week", "3", "--db", db]).exit_code != 0
    assert runner.invoke(app, ["review", "--db", db]).exit_code == 0


def test_doctor_green(settings):
    checks, ok = run_doctor(settings)
    assert ok is True
