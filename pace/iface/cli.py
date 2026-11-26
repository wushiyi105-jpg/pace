"""命令行：seed / zones / week / log / review / suggest / ics / doctor / serve。"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import typer
from rich.console import Console

from ..adapters.store import SqliteStore
from ..app.run import current, export, suggest, zone_table
from ..config import Settings
from ..config import settings as default_settings
from ..doctor import main as doctor_main

app = typer.Typer(help="跑步备赛：配速与周量", no_args_is_help=True)
console = Console()


def _settings(db: Path | None, port: int | None = None) -> Settings:
    s = default_settings.model_copy(deep=True)
    if db:
        s.db_path = db
    if port:
        s.port = port
    return s


def _store(settings: Settings) -> SqliteStore:
    return SqliteStore(settings.db_path)


@app.command()
def seed(db: Path = typer.Option(None)) -> None:
    """写入目标、四周课表与完成记录。"""
    s = _settings(db)
    store = _store(s)
    data = json.loads(
        (Path(__file__).resolve().parents[2] / "data" / "seed.json").read_text(encoding="utf-8")
    )
    g = data["goal"]
    store.set_goal(g["race"], date.fromisoformat(g["on"]), g["distance_km"], g["target_sec"])
    ids = {}
    for i, row in enumerate(data["sessions"], start=1):
        ids[i] = store.add_session(row["week"], date.fromisoformat(row["day"]), row["zone"], row["km"])
    for log in data.get("logs", []):
        store.log(ids[log["session"]], log["km"], log.get("rpe", 5))
    console.print(f"已写入目标 {g['race']}、{len(data['sessions'])} 次课、{len(data.get('logs', []))} 条记录")


@app.command()
def zones(db: Path = typer.Option(None)) -> None:
    """五区间配速表。"""
    store = _store(_settings(db))
    goal = store.goal()
    if goal is None:
        console.print("[red]先 seed[/]")
        raise typer.Exit(code=1)
    console.print(f"{goal.race} {goal.distance_km:g} 公里，目标 {goal.target_sec // 3600}:{goal.target_sec % 3600 // 60:02d}:{goal.target_sec % 60:02d}")
    for z, pace in zone_table(goal).items():
        console.print(f"  {z}  {pace}/公里")


@app.command()
def week(w: int = typer.Option(1, "--week")) -> None:
    """某一周的课表（只读）。"""
    s = _settings(None)
    store = _store(s)
    goal = store.goal()
    rows = [x for x in store.list_sessions() if x.week == w]
    if goal is None or not rows:
        console.print("[red]没有这一周[/]")
        raise typer.Exit(code=1)
    table = zone_table(goal)
    for r in rows:
        console.print(f"{r.day} {r.zone} {r.km:g} 公里 @ {table[r.zone]}/公里  [完成 {store.done_map().get(r.id, 0):g}]")


@app.command()
def log(
    session: int = typer.Option(..., help="课次 id"),
    km: float = typer.Option(..., help="实际公里"),
    rpe: int = typer.Option(5),
    db: Path = typer.Option(None),
) -> None:
    """记一次完成。"""
    store = _store(_settings(db))
    console.print(f"已记 #{store.log(session, km, rpe)}：{km:g} 公里，RPE {rpe}")


@app.command()
def review_cmd(db: Path = typer.Option(None)) -> None:
    """周量、完成率、长距离、扣分。"""
    store = _store(_settings(db))
    r = current(store)
    for w in r.weeks:
        console.print(f"第 {w.week} 周：计划 {w.planned:g}，完成 {w.done:g}（{w.rate:.0%}）")
    for f in r.findings:
        console.print(f"  [yellow]{f.rule_id}[/] -{f.penalty} {f.message}")
    console.print(f"合计扣 {r.penalty_total} 分")


app.command(name="review")(review_cmd)


@app.command()
def suggest_cmd(db: Path = typer.Option(None)) -> None:
    """模型出下周课表（无 key 时打印区间表）。"""
    s = _settings(db)
    store = _store(s)
    rows, findings = suggest(store, s)
    for r in rows:
        console.print(f"{r.get('day')} {r.get('zone')} {r.get('km')} 公里")
    for f in findings:
        console.print(f"  [yellow]{f.rule_id}[/] -{f.penalty} {f.message}")
    if not rows:
        console.print("模型没开，用 zones 看区间")


app.command(name="suggest")(suggest_cmd)


@app.command()
def ics(w: int = typer.Option(1, "--week"), db: Path = typer.Option(None)) -> None:
    """把某一周导出成 ICS。"""
    store = _store(_settings(db))
    try:
        text = export(store, w)
    except ValueError as e:
        console.print(f"[red]{e}[/]")
        raise typer.Exit(code=1)
    Path(f"week{w}.ics").write_text(text, encoding="utf-8", newline="")
    console.print(f"已写 week{w}.ics（{text.count('BEGIN:VEVENT')} 个日程）")


@app.command()
def doctor(db: Path = typer.Option(None)) -> None:
    """四项体检。"""
    raise typer.Exit(code=doctor_main(_settings(db)))


@app.command()
def serve(port: int = typer.Option(None), db: Path = typer.Option(None)) -> None:
    """Web 界面。"""
    import uvicorn

    from .web import create_app

    s = _settings(db, port)
    uvicorn.run(create_app(s), host="127.0.0.1", port=s.port)


if __name__ == "__main__":
    app()
