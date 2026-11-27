"""本周课表卡片：课表、配速、完成率、ICS 一页出。"""

from __future__ import annotations

from datetime import date

from ..domain.catalog import pacing, plans
from ..domain.models import Session
from ..domain.rules.zones import LABELS, zone_pace
from ..ports import LLMPort, StorePort
from .run import WeekRow, build_week, current


def _pace(sec: int) -> str:
    return f"{sec // 60}:{sec % 60:02d}"


def default_week(store: StorePort, today: date | None = None) -> int:
    day = today or date.today()
    rows = store.list_sessions()
    if not rows:
        return 1
    nearest = min(rows, key=lambda s: abs((s.day - day).days))
    return nearest.week


def sessions_for_ics(rows: list[WeekRow], week: int) -> list[Session]:
    return [
        Session(
            row["id"], week, date.fromisoformat(row["day"]),
            row["zone"], row["km"],
        )
        for row in rows
    ]


def build_report(
    store: StorePort, settings, week: int, llm: LLMPort | None = None
) -> tuple[str, list[WeekRow], str]:
    goal = store.goal()
    if goal is None:
        return "# 本周课表\n\n还没有目标，先跑 `seed`。\n", [], "plan"
    rows, findings, source = build_week(store, settings, week, llm)
    review = current(store)
    done = store.done_map()
    planned_total = sum(float(r["km"]) for r in rows)
    prev = next((w.planned for w in review.weeks if w.week == week - 1), 0.0)
    growth = (planned_total - prev) / prev if prev else 0.0
    this = next((w for w in review.weeks if w.week == week), None)
    rate = this.rate if this else 0.0

    days = sorted(str(r["day"]) for r in rows)
    lines = [
        f"# 本周课表 · 第 {week} 周",
        "",
        f"> {goal.race} · {goal.distance_km:g} 公里 · 目标 {_pace(goal.pace_sec)}/公里；"
        f"{'AI 只填日期/区间/公里，配速与表格由本地生成。' if source == 'model' else '本次为本地课表，模型未参与。'}",
        "",
        f"**本周总跑量 {planned_total:g} 公里**",
    ]
    if prev:
        lines.append(
            f"{'⚠️ ' if growth > 0.10 else ''}比上周 {prev:g} 公里{'涨' if growth >= 0 else '降'} "
            f"{abs(growth):.0%}{'，超过 10% 上限，先把量压回去。' if growth > 0.10 else '。'}"
        )
    lines += [
        f"完成率 **{rate:.0%}**；课表从 {days[0] if days else '-'} 到 {days[-1] if days else '-'}。",
        "",
        "## 一、本周课表",
        "",
        "| 日期 | 星期 | 区间 | 公里 | 配速 | 完成 |",
        "| --- | --- | --- | ---: | --- | --- |",
    ]
    for row in rows:
        day = date.fromisoformat(str(row["day"]))
        zone = str(row["zone"])
        km = float(row["km"])
        actual = done.get(row["id"], 0.0)
        done_text = f"已完成 {actual:g} km" if actual else "待跑"
        lines.append(
            f"| {day.month}/{day.day} | 周{'一二三四五六日'[day.weekday()]} | "
            f"{zone} {LABELS[zone]} | {km:g} | {_pace(zone_pace(goal.pace_sec, zone))} | "
            f"{done_text} |"
        )
    lines += [
        "",
        "## 二、本周怎么跑",
        "",
    ]
    for row in rows:
        zone = str(row["zone"])
        lines.append(
            f"- **{row['day']} {LABELS[zone]} {float(row['km']):g} 公里**："
            f"目标配速 {_pace(zone_pace(goal.pace_sec, zone))}/公里。"
        )
    lines += ["", "## 三、完成率回顾与下一步", ""]
    if rate < 0.60:
        lines.append(
            f"- 本周只完成 **{rate:.0%}**：下周总量降到本周计划的 90%，先补齐轻松跑，不补间歇。"
        )
    elif rate > 1.10:
        lines.append("- 完成超过计划 10%：下周不加量，保留一天完全休息。")
    else:
        lines.append("- 完成率在合理区间：按课表推进，周量增幅仍不超过 10%。")
    if growth > 0.10:
        lines.append("- 周量涨幅已超 10%：把最长一次轻松跑砍掉 2-3 公里，别“再坚持一下”。")
    lines.append(f"- 伤病底线：{len(pacing()['injury_rules'])} 条规则已内置，疼痛超过 3 分就停。")
    lines += ["", "## 四、五区间配速", "", "| 区间 | 名称 | 目标配速 |", "| --- | --- | --- |"]
    for zone, label in LABELS.items():
        lines.append(f"| {zone} | {label} | {_pace(zone_pace(goal.pace_sec, zone))}/公里 |")
    lines += [
        "",
        f"> 周期模板库 {len(plans())} 套；本报告按你当前目标与历史完成率排，不套死模板。",
        "",
    ]
    if findings:
        lines += ["## 五、被丢掉的模型行", ""]
        for f in findings:
            lines.append(f"- {f.message}")
        lines.append("")
    return "\n".join(lines), rows, source
